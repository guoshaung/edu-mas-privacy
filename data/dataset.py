"""
数据集配置和工具函数
"""
import json
import random

# 真实的数学知识库
MATH_KNOWLEDGE_BASE = {
    "二次函数": {
        "name": "二次函数",
        "topics": {
            "基础概念": {
                "video": [
                    {
                        "id": "video_001",
                        "title": "二次函数基础概念讲解",
                        "url": "https://www.bilibili.com/video/BV1xx411c7XU",
                        "duration": 600,
                        "difficulty": 0.3,
                        "description": "从定义到图像性质，全面讲解二次函数基础知识"
                    },
                    {
                        "id": "video_002",
                        "title": "二次函数图像性质详解",
                        "url": "https://www.bilibili.com/video/BV1xx411c7XV",
                        "duration": 480,
                        "difficulty": 0.4,
                        "description": "深入讲解二次函数的开口方向、对称轴、顶点等性质"
                    }
                ],
                "interactive": [
                    {
                        "id": "interactive_001",
                        "title": "二次函数图像可视化工具",
                        "url": "https://www.desmos.com/calculator",
                        "duration": 300,
                        "difficulty": 0.35,
                        "description": "在线工具，可调节参数观察图像变化"
                    },
                    {
                        "id": "interactive_002",
                        "title": "GeoGebra 二次函数实验室",
                        "url": "https://www.geogebra.org/m/py2qvyau5v",
                        "duration": 400,
                        "difficulty": 0.4,
                        "description": "动态演示二次函数的平移、缩放等变换"
                    }
                ],
                "exercise": [
                    {
                        "id": "exercise_001",
                        "title": "二次函数顶点坐标练习（基础）",
                        "questions": 10,
                        "difficulty": 0.3,
                        "questions_list": [
                            {"id": 1, "question": "求 y = x² - 4x + 3 的顶点坐标", "options": ["A. (2, -1)", "B. (2, 1)", "C. (-2, -1)", "D. (2, 1)"], "answer": "A", "explanation": "使用顶点公式 x = -b/(2a), y = (4ac-b²)/(4a)"},
                            {"id": 2, "question": "求 y = -x² + 2x + 1 的对称轴", "options": ["A. x = 1", "B. x = -1", "C. x = 2", "D. x = -2"], "answer": "A", "explanation": "对称轴为 x = -b/(2a) = -2/(2×(-1)) = 1"},
                            {"id": 3, "question": "判断 y = 2x² - 8x + 1 的开口方向", "options": ["A. 向上", "B. 向下", "C. 向左", "D: 向右"], "answer": "B", "explanation": "a=2>0, 开口向上"},
                            {"id": 4, "question": "求 y = x² - 4x + 3 与 x 轴交点个数", "options": ["A. 0个", "B. 1个", "C. 2个", "D. 3个"], "answer": "C", "explanation": "判别式 Δ = (-4)² - 4×1×3 = 16 - 12 = 4 > 0, 两个交点"}
                        ]
                    }
                ]
            },
            "进阶应用": {
                "video": [
                    {
                        "id": "video_003",
                        "title": "二次函数最值问题深度解析",
                        "url": "https://www.bilibili.com/video/BV1xx411c7XW",
                        "duration": 720,
                        "difficulty": 0.7,
                        "description: "二次函数在闭区间上的最值求解方法"
                    }
                ],
                "interactive": [
                    {
                        "id": "interactive_003",
                        "title": "二次函数最值可视化工具",
                        "url": "https://www.desmos.com/calculator",
                        "duration": 300,
                        "difficulty": 0.6,
                        "description": "动态演示不同参数下的最值变化"
                    }
                ],
                "exercise": [
                    {
                        "id": "exercise_002",
                        "title": "二次函数综合应用题",
                        "questions": 5,
                        "difficulty": 0.7,
                        "questions_list": [
                            {"id": 1, "question": "某商品利润y与价格x的关系为 y = -x² + 8x - 12，求利润最大时的价格", "options": ["A. 3", "B. 4", "C. 5", "D. 6"], "answer": "B", "explanation": "顶点x = -8/(2×(-1)) = 4，最大利润y = 4"},
                            {"id": 2, "question": "某抛物线 y = -x² + 6x + 5 与 x 轴交点坐标", "options": ["A. (1, 4)", "B. (5, 0)", "C. (1, 4)和(5,0)", "D. (2, 3)"], "answer": "C", "explanation": "解方程 -x² + 6x + 5 = y 和 y = x 得到两个交点"},
                            {"id": 3, "question": "求函数 y = x² - 6x + 10 在区间 [0, 4] 上的最大值", "options": ["A. 0", "B. 1", "C. 4", "D. 10"], "answer": "B", "explanation": "顶点x = 3在区间内，最大值 = f(3) = 1"}
                        ]
                    }
                ]
            }
        }
    },
    "三角函数": {
        "name": "三角函数",
        "topics": {
            "基础概念": {
                "video": [
                    {
                        "id": "trig_video_001",
                        "title": "三角函数基础概念（弧度制）",
                        "url": "https://www.bilibili.com/video/BV1xx411c7XY",
                        "duration": 540,
                        "difficulty": 0.4,
                        "description: "弧度制与角度制的转换，三角函数定义"
                    }
                ],
                "interactive": [
                    {
                        "id": "trig_inter_001",
                        "title: "单位圆交互演示",
                        "url": "https://www.geogebra.org/m/pupuvavmvd",
                        "duration": 300,
                        "difficulty": 0.3,
                        "description: "动态演示三角函数在单位圆上的意义"
                    }
                ],
                "exercise": [
                    {
                        "id": "trig_exercise_001",
                        "title": "三角函数基本计算练习",
                        "questions": 8,
                        "difficulty": 0.35,
                        "questions_list": [
                            {"id": 1, "question": "sin(30°) 的值是？", "options": ["A. 0.5", "B. 0.866", "C. 1", "D. 0.707"], "answer": "A", "explanation": "sin(30°) = 1/2"},
                            {"id": 2, "question": "cos(60°) 的值是？", "options": ["A. 0", "B. 0.5", "C. 1", "D. 0.866"], "answer": "B", "explanation": "cos(60°) = 1/2"},
                            {"id": 3, "question": "tan(45°) 的值是？", "options": ["A. 0.5", "B. 0.707", "C. 1", "D. 1.414"], "answer": "D", "explanation": "tan(45°) = 1"}
                        ]
                    }
                ]
            }
        }
    },
    "一元二次不等式": {
        "name": "一元二次不等式",
        "topics": {
            "基础解法": {
                "video": [
                    {
                        "id": "ineq_video_001",
                        "title": "一元二次不等式解法详解",
                        "url": "https://www.bilibili.com/video/BV1xx411c7xZ",
                        "duration": 660,
                        "difficulty": 0.5,
                        "description": "讲解三种基本解法：配方法、分解因式、图像法"
                    }
                ],
                "exercise": [
                    {
                        "id": "ineq_ex_001",
                        "title": "一元二次不等式练习题",
                        "questions": 6,
                        "difficulty": 0.45,
                        "questions_list": [
                            {"id": 1, "question": "解不等式 x² - 5x + 6 < 0", "options": ["A. (-2, 3)", "B. (-3, 2)", "C. (-∞, -2)∪(3, ∞)", "D. (-∞, -3)∪(2, ∞)"], "answer": "A", "explanation": "方程 x²-5x+6=0的根为x=2或x=3，a=1>0，不等式解集为(-2,3)"},
                            {"id": 2, "question": "解不等式 (x+1)(x-3) ≥ 0", "options": ["A. x≤-1 或 x≥3", "B. -1≤x≤3", "C. x≥-1 且 x≤3", "D. x≤-1 且 x≥3"], "answer": "A", "explanation: "不等式对应的解集是(-∞,-1]∪[3,∞)"}
                        ]
                    }
                ]
            }
        }
    }
}

# 学习风格适配的教学策略
TEACHING_STRATEGIES = {
    'Visual': {
        'name': '视觉型学习者',
        'teaching_methods': [
            '使用图表、图像、可视化工具',
            '多用颜色标注重点',
            '画图帮助理解概念',
            '观看视频教程',
            '使用思维导图'
        ],
        'response_style': '我会尽量用图示和可视化方式来讲解。试着在脑海中画出图像，或者我们找个图表工具来看看。',
        'resource_preference': ['video', 'interactive']
    },
    'Aural': {
        'name': '听觉型学习者',
        'teaching_methods': [
            '口头讲解详细说明',
            '让学生口述思路',
            '播放音频课程',
            '组织讨论',
            '录制讲解回放'
        ],
        'response_style': '我来给你详细讲解一遍。你可以试着把你理解的思路讲给我听，我来帮你完善。',
        'resource_preference': ['audio', 'video']
    },
    'ReadWrite': {
        'name': '读写型学习者',
        'teaching_methods': [
            '整理笔记和总结',
            '阅读教材和文档',
            '做思维导图',
            '写学习日记',
            '列提纲要点'
        ],
        'response_style': '我建议你把这个概念写成笔记，整理出关键点。我们可以一起列个提纲。',
        'resource_preference': ['text', 'exercise']
    },
    'Kinesthetic': {
        'name': '动觉型学习者',
        'teaching_methods': [
            '动手实践操作',
            '使用实物模型',
            '做实验验证',
            '角色扮演',
            '身体动作记忆'
        ],
        'response_style': '让我们动手实践一下！试试做个小实验，或者用实物模型来理解这个概念。',
        'resource_preference': ['interactive', 'exercise']
    }
}

# 常见问题解答库
FAQ_DATABASE = {
    "二次函数顶点公式": {
        "question": "二次函数的顶点公式是什么？",
        "answer": "对于二次函数 y = ax² + bx + c（a≠0），顶点坐标为 (-b/(2a), (4ac-b²)/(4a))",
        "related_topics": ["二次函数图像", "二次函数性质", "配方法"],
        "difficulty": 0.5
    },
    "二次函数开口方向": {
        "question": "如何判断二次函数的开口方向？",
        "answer": "看二次项系数 a：a>0 开口向上，a<0 开口向下",
        "related_topics": ["二次函数图像"],
        "difficulty": 0.3
    },
    "三角函数诱导公式": {
        "question": "如何快速记忆三角函数诱导公式？",
        "answer": "奇变偶不变，符号看象限：一全正，二正弦正，三正切余，四余弦余",
        "related_topics": ["三角函数基础", "诱导公式推导"],
        "difficulty": 0.6
    }
}

# 学习路径推荐
LEARNING_PATHS = {
    "二次函数初学者": {
        "steps": [
            {"topic": "二次函数定义", "duration": 30, "resources": ["video_001"]},
            {"topic": "二次函数图像", "duration": 40, "resources": ["video_002", "interactive_001"]},
            {"topic": "顶点坐标公式", "duration": 25, "resources": ["video_003"]},
            {"topic": "基础练习", "duration": 20, "resources": ["exercise_001"]}
        ],
        "total_time": 115
    },
    "二次函数进阶": {
        "steps": [
            {"topic": "二次函数最值问题", "duration": 45, "resources": ["video_003", "interactive_003"]},
            {"        "topic": "二次函数综合应用", "duration": 60, "resources": ["exercise_002"]},
            {"topic": "实际应用问题", "duration": 40, "resources": []}
        ],
        "total_time": 145
    }
}

# 学生学习状态模拟
STUDENT_PROGRESS = {
    "student_20240313_001": {
        "name": "张同学",
        "grade": 9,
        "learning_style": "Visual",
        "progress": {
            "二次函数": {
                "total_topics": 14,
                "mastered_topics": 12,
                "current_topic": "最值问题",
                "score_history": [65, 72, 78, 80, 85, 87],
                "weak_points": ["最值应用", "综合题"]
            },
            "三角函数": {
                "total_topics": 10,
                "mastered_topics": 5,
                "current_topic": "诱导公式",
                "score_history": [45, 50, 52, 55, 60],
                "weak_points": ["诱导公式", "图像变换"]
            },
            "一元二次不等式": {
                "total_topics": 5,
                "mastered_topics": 1,
                "current_topic": "解法步骤",
                "score_history": [40, 42, 45],
                "weak_points": ["分解因式", "图像法"]
            }
        },
        "learning_goals": ["提高综合应用能力", "掌握最值问题"],
        "recent_errors": [
            {
                "topic": "二次函数最值",
                "error": "不会求含参数的最值",
                "timestamp": "2026-03-13 22:30:00"
            }
        ]
    }
}

# 虺能辅导对话模板
TUTORING_TEMPLATES = {
    "Visual": {
        "greeting": "你好！我看到你是视觉型学习者。我们可以用图像和可视化工具来学习概念，这样会更容易理解。",
        "scaffolding": "试着在脑海里画个图看看。你能在脑海中想象这个函数的形状吗？",
        "hint": "观察图像的变化趋势，能发现什么规律？",
        "encouragement": "很好的观察！这就是视觉学习的优势，你能把看到的规律总结一下吗？",
        "resources": "我可以推荐一些可视化工具和视频课程，帮你更直观地理解。"
    },
    "Aural": {
        "greeting": "你好！我看你偏好听觉学习。那我们就多聊聊，我来给你讲解这个知识点。",
        "scaffolding": "试着把你理解的思路讲给我听听，我来帮你完善。",
        "hint": "可以把这个概念用自己的话复述一遍，我来确认是否理解正确。",
        "encouragement": "表达得很清楚！看来你已经掌握了核心概念。",
        "resources": "我为你推荐一些音频课程和讲解视频。"
    },
    "ReadWrite": {
        "greeting": "你好！我看你擅长读写。那我们来做笔记和总结，这样能帮助你更好地理解和记忆。",
        "scaffolding": "把关键概念写下来，列个提纲试试看。",
        "hint": "可以试着把这个知识点的要点列出来，我来帮你检查是否完整。",
        "encouragement": "笔记做得很好！这样整理知识点非常系统化。",
        "resources": "我推荐你阅读教材上的相关章节，加深理解。"
    },
    "Kinesthetic": {
        "greeting": "你好！看来你喜欢动手实践。那我们来做实验和实践操作来学习！",
        "scaffolding": "让我们动手试试这个实验，观察发生了什么。",
        "hint": "试着调整参数看看结果如何变化，能发现什么规律？",
        "encouragement": "实验很成功！通过实践你已经理解了核心概念。",
        "resources = "我推荐一些交互式实验工具，让你亲手验证学到的知识。"
    }
}

def get_teaching_strategy(learning_style):
    """根据学习风格获取教学策略"""
    return TEACHING_STRATEGIES.get(learning_style, TEACHING_STRATEGIES['Visual'])

def get_resources_by_topic(topic, difficulty, style, count=3):
    """根据知识点、难度和风格获取资源"""
    resources = []
    
    # 在知识库中查找
    for subject_name, subject_data in MATH_KNOWLEDGE_BASE.items():
        for topic_name, topic_data in subject_data['topics'].items():
            if topic in topic_name or topic_name in topic_name:
                # 匹配难度
                matched_resources = []
                for res_type in ['video', 'interactive', 'exercise']:
                    for res in topic_data.get(res_type, []):
                        if abs(res['difficulty'] - difficulty) <= 0.2:
                            matched_resources.append(res)
                
                # 根据学习风格过滤
                style_priority = {
                    'Visual': ['video', 'interactive', 'exercise'],
                    'Aural': ['video'],
                    'ReadWrite': ['exercise'],
                    'Kinesthetic': ['interactive', 'exercise']
                }
                
                priority = style_priority.get(style, ['video', 'interactive', 'exercise'])
                
                # 排序并取前count个
                sorted_resources = sorted(
                    matched_resources,
                    key=lambda x: priority.index(x.get('type', 'video')) if x.get('type') in priority else 99
                )
                
                resources.extend(sorted_resources[:count])
                
                if resources:
                    return resources
    
    return []

def get_learning_path(student_id):
    """获取学习路径"""
    return LEARNING_PATHS.get(student_id, LEARNING_PATHS["二次函数初学者"])

def get_student_progress(student_id):
    """获取学生进度"""
    return STUDENT_PROGRESS.get(student_id, {
        "name": "新学生",
        "grade": 9,
        "learning_style": "Mixed",
        "progress": {
            "二次函数": {
                "total_topics": 14,
                "mastered_topics": 0,
                "score_history": []
            }
        },
        "learning_goals": [],
        "recent_errors": []
    })

def save_student_progress(student_id, progress_data):
    """保存学生进度"""
    if student_id not in STUDENT_PROGRESS:
        STUDENT_PROGRESS[student_id] = {
            "name": "新学生",
            "grade": 9,
            "learning_style": "Mixed",
            "progress": {},
            "learning_goals": [],
            "recent_errors": [],
            "created_at": datetime.now().isoformat()
        }
    
    # 更新进度
    STUDENT_PROGRESS[student_id].update(progress_data)
    
    # 保存到文件
    with open('data/student_progress.json', 'w', encoding='utf-8') as f:
        json.dump(STUDENT_PROGRESS, f, ensure_ascii=False, indent=2)
