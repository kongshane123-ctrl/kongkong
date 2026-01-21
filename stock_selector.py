# -*- coding: utf-8 -*-
import efinance as ef
import pandas as pd
import numpy as np
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
import warnings

# 忽略警告信息，保持界面清爽
warnings.filterwarnings('ignore')

# 1. 配置参数
CONFIG = {
    'min_amount': 50000000,   # 最小成交额 5000万
    'max_pe': 60,             # 最大市盈率 60
    'thread_num': 8,          # 线程数
    'filename': 'My_Stock_List.xlsx' # 结果文件名
}

def _summarize_proxy_env():
    proxy_keys = ["HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "NO_PROXY"]
    proxy_values = {key: os.environ.get(key) for key in proxy_keys if os.environ.get(key)}
    if not proxy_values:
        return "未检测到代理环境变量。"
    summary = ", ".join([f"{key}={value}" for key, value in proxy_values.items()])
    return f"检测到代理环境变量: {summary}"


def get_data_safe():
    print(">>> [1/3] 正在获取全市场数据...")
    # 获取快照
    try:
        df = ef.stock.get_realtime_quotes()
    except Exception as exc:
        proxy_hint = _summarize_proxy_env()
        raise RuntimeError(
            "获取实时行情失败，通常是网络/代理导致的连接问题。"
            f"{proxy_hint} 请检查网络连接或关闭代理后重试。"
        ) from exc
    
    # 重命名列（标准化）
    rename_map = {
        '股票代码': 'code', '股票名称': 'name', '最新价': 'price',
        '动态市盈率': 'pe', '市净率': 'pb', '成交额': 'amount',
        '总市值': 'mkt_cap', '涨跌幅': 'change_pct'
    }
    df = df.rename(columns=rename_map)
    
    # --- 关键修复：防止报错 ---
    # 如果数据源里缺了某列（比如 PB），我们自动填空值，不让程序崩馈
    needed_cols = ['price', 'pe', 'pb', 'amount', 'mkt_cap']
    for col in needed_cols:
        if col not in df.columns:
            print(f"    (自动修复) 缺失字段: {col}，已补全为空值")
            df[col] = np.nan
            
    # 转成数字格式
    for col in needed_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')
        
    return df

def run_strategy():
    # 1. 获取数据
    df = get_data_safe()
    print(f"    获取到 {len(df)} 只股票")

    # 2. 初步筛选
    print(">>> [2/3] 正在执行筛选...")
    
    # 剔除 ST
    df = df[~df['name'].str.contains('ST', na=False)]
    
    # 剔除停牌 (价格为0)
    df = df[df['price'] > 0]
    
    # 核心筛选：成交额 > 5000万 且 PE < 60 (或者PE为空也保留)
    mask_liq = df['amount'] > CONFIG['min_amount']
    mask_pe = (df['pe'] < CONFIG['max_pe']) | df['pe'].isna()
    
    df_final = df[mask_liq & mask_pe].copy()
    
    # 3. 简单打分排序 (综合 估值+流动性)
    # 分数越高越好
    score_pe = (1 - df_final['pe'].rank(pct=True)) * 50  # PE越低分越高
    score_liq = df_final['amount'].rank(pct=True) * 50   # 成交额越高分越高
    
    df_final['Score'] = score_pe + score_liq
    df_final = df_final.sort_values('Score', ascending=False)

    # 4. 导出
    print(">>> [3/3] 正在导出 Excel...")
    output_cols = ['code', 'name', 'Score', 'price', 'pe', 'pb', 'amount']
    # 只导出存在的列
    cols = [c for c in output_cols if c in df_final.columns]
    
    try:
        df_final[cols].to_excel(CONFIG['filename'], index=False)
        print(f"\n✅ 成功了！请在桌面查看文件: {CONFIG['filename']}")
        print(f"    筛选出: {len(df_final)} 只股票")
        print("\n前 5 名预览:")
        print(df_final[cols].head(5).to_string())
    except Exception as e:
        print(f"❌ 导出失败: {e}")

if __name__ == '__main__':
    run_strategy()
