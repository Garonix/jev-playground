from typing import Any, Dict, List
from typesafe_sdk import Choice, Noul

CASE_META = {
    "id": "smart_home",
    "title": "智能家居",
    "english_title": "Smart Home",
    "official_url": "https://docs.typesafe.ai/demos/smart-home",
    "pattern": "推测性展开",
    "badge": "官方案例",
    "summary": "单次请求并行下发分类、设备与推测性动作，取代多轮串行调用。",
    "default_input_zh": {
        "user_request": "把屋里所有的灯都关掉"
    },
    "default_input_en": {
        "user_request": "Turn off all of the lights in the house"
    },
    "presets_zh": [
        { "name": "全屋关灯", "data": { "user_request": "把屋里所有的灯都关掉" } },
        { "name": "空调调温", "data": { "user_request": "帮我把客厅的空调打开，温度调到24度" } },
        { "name": "主卧调光", "data": { "user_request": "我要在主卧看电影了，帮我把卧室灯光调暗一点" } },
        { "name": "复合指令", "data": { "user_request": "把阳台灯关掉，同时启动扫地机器人开始全屋清扫" } },
        { "name": "天气询问", "data": { "user_request": "明天的天气怎么样？出门需要带雨伞吗？" } }
    ],
    "presets_en": [
        { "name": "Turn off lights", "data": { "user_request": "Turn off all of the lights in the house" } },
        { "name": "Adjust AC temp", "data": { "user_request": "Turn on the living room AC and set temperature to 24 degrees" } },
        { "name": "Dim bedroom light", "data": { "user_request": "Dim the lights in the master bedroom for movie night" } },
        { "name": "Compound command", "data": { "user_request": "Turn off balcony lights and start the robot vacuum to clean the house" } },
        { "name": "Weather query", "data": { "user_request": "What is the weather like tomorrow? Do I need an umbrella?" } }
    ]
}

def get_questions_spec(lang: str = "zh") -> List[Dict[str, Any]]:
    if lang == "zh":
        return [
            {
                "id": "请求类别",
                "type": "choice",
                "instructions": "该用户请求属于什么类别？",
                "criteria": {
                    "设备控制": "控制灯光、空调、扫地机、音响等智能家居物理设备的直接指令",
                    "信息查询": "查询常规信息、天气预报或通用知识",
                    "日常闲聊": "日常闲聊、打招呼、问候或对话"
                }
            },
            {
                "id": "目标区域",
                "type": "choice",
                "instructions": "该请求针对哪个房屋空间或区域？",
                "criteria": {
                    "全屋": "全屋、所有房间或整套房屋",
                    "客厅": "客厅或主厅",
                    "卧室": "卧室或主卧",
                    "厨房": "厨房或餐厅",
                    "阳台": "阳台",
                    "未指定": "未提及具体房间"
                }
            },
            {
                "id": "设备类型",
                "type": "choice",
                "instructions": "该请求针对哪类硬件设备或家电？",
                "criteria": {
                    "灯光": "灯光、吊灯、筒灯或开关",
                    "空调": "空调、温控器、暖气或风扇",
                    "扫地机": "扫地机器人或地面清洁设备",
                    "影音": "电视、音响或播放器",
                    "无": "不涉及任何智能家居设备"
                }
            },
            {
                "id": "灯光动作",
                "type": "choice",
                "instructions": "若该请求针对灯光，具体执行何种动作？",
                "criteria": {
                    "关灯": "关灯、熄灭或切断电源",
                    "开灯": "开灯、点亮或通电",
                    "调暗": "调暗、降低亮度或进入夜间模式",
                    "无": "不涉及灯光动作"
                }
            },
            {
                "id": "空调动作",
                "type": "choice",
                "instructions": "若该请求针对空调温控，具体执行何种动作？",
                "criteria": {
                    "开机": "开机或启动制冷/制热",
                    "关机": "关机或停止运行",
                    "调温": "调节或设定目标温度",
                    "无": "不涉及空调动作"
                }
            },
            {
                "id": "是否复合指令",
                "type": "noul",
                "instructions": "该请求是否包含两个或两个以上独立的动作或指令？"
            }
        ]
    else:
        return [
            {
                "id": "category",
                "type": "choice",
                "instructions": "What category of user request is this?",
                "criteria": {
                    "smarthome_command": "A direct command to control smart home devices like lights, climate, vacuum, or media",
                    "query": "A request for general information, weather forecast, or factual search",
                    "conversation": "Casual chitchat, greeting, jokes, or conversational dialogue"
                }
            },
            {
                "id": "target_domain",
                "type": "choice",
                "instructions": "What location or room domain is this request targeting?",
                "criteria": {
                    "whole_house": "The entire house, all rooms, or the whole apartment",
                    "living_room": "Living room or main hall",
                    "bedroom": "Bedroom or master bedroom",
                    "kitchen": "Kitchen or dining room",
                    "balcony": "Balcony or patio",
                    "unspecified": "No specific room or location mentioned"
                }
            },
            {
                "id": "device_type",
                "type": "choice",
                "instructions": "What type of appliance or hardware device is this request targeting?",
                "criteria": {
                    "lights": "Lighting, lamps, bulbs, chandeliers, or switches",
                    "climate": "Air conditioner, thermostat, heater, fan",
                    "vacuum": "Robot vacuum cleaner, sweeper, or cleaning appliance",
                    "media": "TV, speakers, music player, screen",
                    "none": "Not targeting any physical smart home device"
                }
            },
            {
                "id": "action_lights",
                "type": "choice",
                "instructions": "Assuming this request targets lights, what specific action should be executed?",
                "criteria": {
                    "turn_off": "Turn off, switch off, or extinguish the light(s)",
                    "turn_on": "Turn on, power on, or illuminate the light(s)",
                    "dim": "Dim brightness, lower luminosity, or enter night mode",
                    "none": "No action related to lights"
                }
            },
            {
                "id": "action_climate",
                "type": "choice",
                "instructions": "Assuming this request targets climate or AC, what specific action should be executed?",
                "criteria": {
                    "turn_on": "Power on or start the air conditioner/heater",
                    "turn_off": "Power off or stop the air conditioner/heater",
                    "set_temperature": "Set, raise, or lower temperature",
                    "none": "No action related to climate"
                }
            },
            {
                "id": "is_compound",
                "type": "noul",
                "instructions": "Does this request ask for more than one distinct action or command?"
            }
        ]

def build_questions(input_data: Dict[str, Any], lang: str = "zh") -> tuple[Any, Dict[str, Any]]:
    state = {
        "user_request": input_data.get("user_request", "")
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
    cat_ans = answers.get("请求类别") or answers.get("category") or {}
    category = cat_ans.get("choice", "unknown")
    cat_conf = cat_ans.get("confidence", 0.0)
    
    is_compound_ans = answers.get("是否复合指令") or answers.get("is_compound") or {}
    compound_prob = is_compound_ans.get("noul", 0.0)
    
    device_ans = answers.get("设备类型") or answers.get("device_type") or {}
    device = device_ans.get("choice", "none")
    
    domain_ans = answers.get("目标区域") or answers.get("target_domain") or {}
    domain = domain_ans.get("choice", "未指定")
    
    actions = []
    status_tag = "success"
    
    is_command = category in ["设备控制", "smarthome_command"]
    
    if compound_prob > 0.6:
        status_tag = "warning"
        headline = "复合指令"
        detail = f"复合指令概率 {compound_prob:.1%}，需触发指令拆解管道。"
        actions.append({"action": "拆解指令", "target": "CommandQueue"})
    elif not is_command:
        status_tag = "info"
        headline = "转接对话模型"
        detail = f"类别为 {category} (置信度 {cat_conf:.1%})，透传至通用大模型。"
        actions.append({"action": "转接对话", "intent": category})
    else:
        headline = f"硬件控制: {domain} / {device}"
        detail = f"识别为设备控制指令 (置信度 {cat_conf:.1%})。"
        
        if device in ["灯光", "lights"]:
            act_ans = answers.get("灯光动作") or answers.get("action_lights") or {}
            act = act_ans.get("choice", "unknown")
            actions.append({
                "action": f"Light.{act}",
                "domain": domain,
                "confidence": act_ans.get("confidence", 0.0)
            })
        elif device in ["空调", "climate"]:
            act_ans = answers.get("空调动作") or answers.get("action_climate") or {}
            act = act_ans.get("choice", "unknown")
            actions.append({
                "action": f"Climate.{act}",
                "domain": domain,
                "confidence": act_ans.get("confidence", 0.0)
            })
        else:
            actions.append({
                "action": f"Device.{device}",
                "domain": domain
            })

    return {
        "headline": headline,
        "status_tag": status_tag,
        "detail": detail,
        "actions": actions
    }
