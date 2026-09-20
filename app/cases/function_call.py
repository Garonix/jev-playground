from typing import Any, Dict, List
from typesafe_sdk import Choice, Noul

CASE_META = {
    "id": "function_call",
    "title": "函数调用",
    "english_title": "Function Calling",
    "official_url": "https://docs.typesafe.ai/cookbooks/function_calling",
    "pattern": "参数绑定",
    "badge": "官方案例",
    "summary": "将自然语言指令映射为强类型函数与闭集枚举参数。",
    "default_input_zh": {
        "command": "帮我画一下英伟达(NVDA)过去3个月日K线，叠加上50日均线与成交量"
    },
    "default_input_en": {
        "command": "plot rolling correlation between nvda and spy for the past month"
    },
    "presets_zh": [
        { "name": "K线与均线", "data": { "command": "绘制英伟达(NVDA)过去3个月日K线，叠加上50日均线与成交量" } },
        { "name": "滚动相关性", "data": { "command": "计算英伟达(NVDA)和标普500(SPY)过去一个月的滚动相关性" } },
        { "name": "收益率对比", "data": { "command": "对比苹果(AAPL)、特斯拉(TSLA)和微软过去半年的收益率" } },
        { "name": "大盘概览", "data": { "command": "查看今天美股标普500大盘日内概况与涨跌分布" } }
    ],
    "presets_en": [
        { "name": "Plot candles", "data": { "command": "plot NVDA price candles for the past 3 months with 50 moving average and volume" } },
        { "name": "Rolling correlation", "data": { "command": "plot rolling correlation between nvda and spy for the past month" } },
        { "name": "Compare returns", "data": { "command": "compare returns for AAPL, TSLA and MSFT over the past 6 months" } },
        { "name": "Market summary", "data": { "command": "give me the market summary for S&P 500 index today" } }
    ]
}

def get_questions_spec(lang: str = "zh") -> List[Dict[str, Any]]:
    if lang == "zh":
        return [
            {
                "id": "匹配目标函数",
                "type": "choice",
                "instructions": "`command` 中用户的意图匹配哪项分析或交易工具函数？",
                "criteria": {
                    "计算相关性": "计算并绘制股票与基准指数的滚动相关系数",
                    "绘制行情图": "绘制单只股票的走势图、K线图或分时图",
                    "收益率对比": "横向对比多只股票的累计收益率表现",
                    "大盘全天概览": "查看大盘全天走势概览与核心指标",
                    "未匹配": "未匹配任何已知量化函数"
                }
            },
            {
                "id": "标的资产代码",
                "type": "choice",
                "instructions": "`command` 涉及的主要股票代码是哪一只？",
                "criteria": {
                    "NVDA": "英伟达 (NVDA)",
                    "AAPL": "苹果 (AAPL)",
                    "MSFT": "微软 (MSFT)",
                    "TSLA": "特斯拉 (TSLA)",
                    "SPY": "标普500 ETF (SPY)",
                    "无": "未提及具体单一股票"
                }
            },
            {
                "id": "对比基准指数",
                "type": "choice",
                "instructions": "相关性或对比分析中引用的基准指数是哪个？",
                "criteria": {
                    "SPY": "标普500指数 ETF",
                    "QQQ": "纳斯达克100 ETF",
                    "无": "未提及基准指数"
                }
            },
            {
                "id": "时间历史窗口",
                "type": "choice",
                "instructions": "用户指定的时间窗口或历史周期是多长？",
                "criteria": {
                    "1天": "一天或当天",
                    "1周": "一周或过去7天",
                    "1个月": "一个月或近30天",
                    "3个月": "三个月或一季度",
                    "半年": "半年",
                    "1年": "一年"
                }
            },
            {
                "id": "图表形态类型",
                "type": "choice",
                "instructions": "用户要求绘制K线蜡烛图还是简单折线走势？",
                "criteria": {
                    "K线蜡烛图": "K线蜡烛图或OHLC柱",
                    "普通折线": "普通收盘价折线走势"
                }
            },
            {
                "id": "叠加均线周期",
                "type": "choice",
                "instructions": "需要叠加上哪种均线周期？",
                "criteria": {
                    "不叠加": "不需要均线",
                    "9日线": "9周期短期均线",
                    "20日线": "20周期均线",
                    "50日线": "50周期长线均线"
                }
            },
            {
                "id": "是否显示成交量",
                "type": "noul",
                "instructions": "指令是否要求显示成交量柱线？"
            }
        ]
    else:
        return [
            {
                "id": "target_function",
                "type": "choice",
                "instructions": "Which trading/analysis tool function matches the user's intent in `command`?",
                "criteria": {
                    "rolling_correlation": "Plot or calculate rolling correlation between a stock and a benchmark",
                    "plot_price": "Draw price chart, candlesticks, or OHLC chart for a single stock symbol",
                    "compare_returns": "Compare cumulative return or price performance among multiple stock tickers",
                    "market_summary": "Provide broad market overview, index movements, or daily summary",
                    "unknown": "None of the supported trading functions match the command"
                }
            },
            {
                "id": "symbol",
                "type": "choice",
                "instructions": "Which primary stock ticker symbol is the main subject of `command`?",
                "criteria": {
                    "NVDA": "NVIDIA Corporation (NVDA)",
                    "AAPL": "Apple Inc. (AAPL)",
                    "MSFT": "Microsoft Corporation (MSFT)",
                    "TSLA": "Tesla Inc. (TSLA)",
                    "SPY": "S&P 500 ETF Trust (SPY)",
                    "none": "No specific single stock symbol mentioned"
                }
            },
            {
                "id": "benchmark",
                "type": "choice",
                "instructions": "Assuming correlation or comparison, which benchmark index is referenced?",
                "criteria": {
                    "SPY": "S&P 500 Index ETF (SPY)",
                    "QQQ": "Invesco QQQ Trust / Nasdaq 100",
                    "none": "No benchmark explicitly mentioned"
                }
            },
            {
                "id": "window",
                "type": "choice",
                "instructions": "What time window or historical duration does the user specify?",
                "criteria": {
                    "1d": "One day or today",
                    "1w": "One week or past 7 days",
                    "1mo": "One month or past 30 days",
                    "3mo": "Three months or one quarter",
                    "6mo": "Six months or half year",
                    "1y": "One year or past 12 months"
                }
            },
            {
                "id": "chart_style",
                "type": "choice",
                "instructions": "Does the user request candles or a simple line chart?",
                "criteria": {
                    "candles": "Candlestick, K-line, or OHLC bars",
                    "line": "Simple price line or default curve"
                }
            },
            {
                "id": "moving_average",
                "type": "choice",
                "instructions": "Which moving average window (SMA) is requested, if any?",
                "criteria": {
                    "none": "No moving average requested",
                    "9": "9-period short moving average",
                    "20": "20-period moving average",
                    "50": "50-period long-term moving average"
                }
            },
            {
                "id": "include_volume",
                "type": "noul",
                "instructions": "Does the command ask to include or display trading volume?"
            }
        ]

def build_questions(input_data: Dict[str, Any], lang: str = "zh") -> tuple[Any, Dict[str, Any]]:
    state = {
        "command": input_data.get("command", "")
    }
    spec = get_questions_spec(lang)
    questions = {}
    for item in spec:
        q_id = item["id"]
        q_type = item["type"]
        if q_type == "choice":
            questions[q_id] = Choice(instructions=item["instructions"], criteria=item["criteria"])
        elif q_type == "noul":
            questions[q_id] = Noul(instructions=item["instructions"])
            
    return state, questions

def process_workflow(answers: Dict[str, Any]) -> Dict[str, Any]:
    fn_ans = answers.get("匹配目标函数") or answers.get("target_function") or {}
    fn_name = fn_ans.get("choice", "unknown")
    fn_conf = fn_ans.get("confidence", 0.0)
    
    sym_ans = answers.get("标的资产代码") or answers.get("symbol") or {}
    symbol = sym_ans.get("choice", "none")
    
    bench_ans = answers.get("对比基准指数") or answers.get("benchmark") or {}
    benchmark = bench_ans.get("choice", "none")
    
    win_ans = answers.get("时间历史窗口") or answers.get("window") or {}
    window = win_ans.get("choice", "1mo")
    
    style_ans = answers.get("图表形态类型") or answers.get("chart_style") or {}
    style = style_ans.get("choice", "line")
    
    ma_ans = answers.get("叠加均线周期") or answers.get("moving_average") or {}
    ma = ma_ans.get("choice", "none")
    
    vol_ans = answers.get("是否显示成交量") or answers.get("include_volume") or {}
    include_vol = vol_ans.get("noul", 0.0) >= 0.55
    
    if fn_name in ["计算相关性", "rolling_correlation"]:
        b = benchmark if benchmark not in ["none", "无"] else "SPY"
        call_code = f"rolling_correlation(symbol='{symbol}', benchmark='{b}', window='{window}')"
        headline = "绑定: rolling_correlation()"
        detail = f"标的 {symbol}，基准 {b}，周期 {window}。"
    elif fn_name in ["绘制行情图", "plot_price"]:
        ma_param = f", ma={ma}" if ma not in ["none", "不叠加"] else ""
        vol_param = f", volume=True" if include_vol else ""
        call_code = f"plot_price(symbol='{symbol}', window='{window}', style='{style}'{ma_param}{vol_param})"
        headline = "绑定: plot_price()"
        detail = f"标的 {symbol}，周期 {window}，形态 {style}。"
    elif fn_name in ["收益率对比", "compare_returns"]:
        call_code = f"compare_returns(primary='{symbol}', window='{window}')"
        headline = "绑定: compare_returns()"
        detail = f"标的 {symbol}，周期 {window}。"
    elif fn_name in ["大盘全天概览", "market_summary"]:
        call_code = "market_summary(index='SPY')"
        headline = "绑定: market_summary()"
        detail = "大盘日内指标概览。"
    else:
        call_code = "# 未匹配到量化函数"
        headline = "未命中函数"
        detail = "未能匹配已知函数特征。"

    return {
        "headline": headline,
        "status_tag": "success" if fn_name not in ["unknown", "未匹配"] else "warning",
        "detail": detail,
        "generated_code": call_code,
        "actions": [{"action": call_code, "confidence": round(fn_conf, 3)}]
    }
