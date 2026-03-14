"""
简化的REST API服务器
不依赖复杂库，直接提供智能回复
"""
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import random
import time
from urllib.parse import urlparse, parse_qs


class EducationAPIHandler(BaseHTTPRequestHandler):
    """教育平台API处理器"""

    def _set_headers(self, status_code=200):
        """设置响应头"""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_OPTIONS(self):
        """处理OPTIONS请求（CORS预检）"""
        self._set_headers(200)

    def do_GET(self):
        """处理GET请求"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path

        if path == '/health':
            self._set_headers(200)
            self.wfile.write(json.dumps({
                "status": "healthy",
                "services": {
                    "rest_api": "running",
                    "ai_tutor": "running"
                }
            }).encode())

        elif path == '/api/teacher/students':
            self._set_headers(200)
            students = [
                {"id": "stu_001", "name": "张同学", "grade": 9, "style": "Visual", "progress": 85, "weak_points": ["最值应用", "综合题"], "last_active": "2分钟前"},
                {"id": "stu_002", "name": "李同学", "grade": 9, "style": "Aural", "progress": 72, "weak_points": ["概念理解", "公式记忆"], "last_active": "5分钟前"},
                {"id": "stu_003", "name": "王同学", "grade": 10, "style": "Kinesthetic", "progress": 68, "weak_points": ["基础计算", "几何证明"], "last_active": "10分钟前"}
            ]
            self.wfile.write(json.dumps({"success": True, "data": students}).encode())

        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({"error": "Not found"}).encode())

    def do_POST(self):
        """处理POST请求"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path

        if path == '/api/student/message':
            try:
                # 读取请求数据
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))

                message = data.get('message', '')
                learning_style = data.get('learning_style', 'Visual')

                # 生成智能回复
                response = self.generate_ai_response(message, learning_style)

                self._set_headers(200)
                self.wfile.write(json.dumps({
                    "success": True,
                    "data": {
                        "response": response,
                        "metadata": {
                            "learning_style": learning_style,
                            "timestamp": time.time()
                        }
                    }
                }).encode())

            except Exception as e:
                self._set_headers(500)
                self.wfile.write(json.dumps({
                    "success": False,
                    "error": str(e)
                }).encode())

        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({"error": "Not found"}).encode())

    def generate_ai_response(self, student_message, learning_style):
        """
        生成基于学习风格的智能辅导回复
        这里模拟AI的思考过程
        """
        message_lower = student_message.lower()

        # 识别问题类型
        if '二次函数' in student_message or '顶点' in student_message:
            return self.generate_quadratic_response(student_message, learning_style)
        elif '三角函数' in student_message or '正弦' in student_message or '余弦' in student_message:
            return self.generate_trig_response(student_message, learning_style)
        elif '不懂' in student_message or '不会' in student_message or '难' in student_message:
            return self.generate_concept_help_response(student_message, learning_style)
        elif '作业' in student_message or '题目' in student_message or '练习' in student_message:
            return self.generate_homework_help_response(student_message, learning_style)
        elif '例子' in student_message or '例题' in student_message:
            return self.generate_example_response(student_message, learning_style)
        else:
            return self.generate_general_response(student_message, learning_style)

    def generate_quadratic_response(self, message, style):
        """二次函数相关的智能回复"""
        if style == 'Visual':
            return """很好！二次函数确实是一个重要概念。让我们用图像来理解：

**顶点公式的几何意义：**

对于二次函数 y = ax² + bx + c

1. **图像特征**：抛物线开口由a决定
   - a > 0：开口向上（像笑脸😊）
   - a < 0：开口向下（像哭脸😢）

2. **顶点坐标**：(-b/2a, f(-b/2a))
   - 这是抛物线的"最高点"或"最低点"
   - 对称轴就是 x = -b/2a

3. **视觉理解方法**：
   - 试着画几个不同a值的抛物线
   - 观察顶点位置的变化规律
   - 用不同颜色标出对称轴

**思考题：**
• 如果a=2，b=4，顶点x坐标是多少？
• 你能画出y = x² - 4x + 3的图像吗？

建议：拿纸笔画画看，图像会帮你更好地理解！"""
        elif style == 'Aural':
            return """我来给你详细讲解二次函数顶点公式的含义：

**首先理解顶点的重要性：**
顶点是二次函数图像（抛物线）的"转折点"，它告诉我们函数的最大值或最小值在哪里。

**顶点公式的推导思路：**
1. 我们要找到抛物线的对称轴
2. 对称轴上的点就是顶点
3. 通过配方法可以得到公式

**记忆技巧：**
- x坐标：-b ÷ (2a)
- y坐标：把x坐标代回原式计算

你可以这样理解：就像找队伍的中心位置一样，顶点就是抛物线的"中心"。

**我们来练习一下：**
如果我说y = 2x² + 8x + 5，你能告诉我：
1. 这个抛物线开口向上还是向下？
2. 顶点的x坐标在哪里？

试着说说你的思路，我来帮你纠正！"""
        else:  # ReadWrite or Kinesthetic
            return """让我们系统地学习二次函数顶点公式：

**核心公式：**
对于 y = ax² + bx + c
顶点坐标为：(-b/2a, f(-b/2a))

**详细步骤：**

1️⃣ **确定参数**
   - a：二次项系数
   - b：一次项系数
   - c：常数项

2️⃣ **计算顶点x坐标**
   公式：x = -b/(2a)

3️⃣ **计算顶点y坐标**
   将x代入原函数：y = a(-b/2a)² + b(-b/2a) + c

**实例演示：**
求 y = x² - 4x + 3 的顶点

解：a=1, b=-4, c=3
- x = -(-4)/(2×1) = 4/2 = 2
- y = 2² - 4×2 + 3 = 4 - 8 + 3 = -1
- 顶点：(2, -1)

**练习建议：**
1. 做5道不同类型的练习题
2. 把每一步都写下来
3. 总结常见错误

你现在可以试试这个题目：y = 2x² + 4x - 1"""

    def generate_trig_response(self, message, style):
        """三角函数相关的回复"""
        return """关于三角函数，这是个很好的问题！

**核心概念：**
三角函数描述了角度和比例之间的关系。

**建议的学习方法：**
1. 先记住单位圆的定义
2. 理解正弦、余弦的几何意义
3. 多做练习巩固

你可以先说说：具体哪个概念不太清楚？是定义、公式，还是应用？"""

    def generate_concept_help_response(self, message, style):
        """概念理解的辅导"""
        return """我理解你的困惑！数学概念确实需要时间消化。

**学习建议：**
1. **不要着急**：理解比记忆更重要
2. **多角度思考**：用不同方式理解同一个概念
3. **动手实践**：通过练习来加深理解

**具体建议：**
- 能告诉我具体是哪个概念让你困惑吗？
- 我们可以从最基础的部分开始，逐步深入

记住：每个数学家都是从"不懂"开始的！"""

    def generate_homework_help_response(self, message, style):
        """作业帮助"""
        return """好的，我来帮你解决作业问题！

**解题思路：**
1. 先理解题目在问什么
2. 回忆相关的知识点
3. 确定解题方法
4. 一步步计算
5. 检查答案

你可以把具体题目发给我，我给你提供思路引导。我不会直接给答案，而是帮你理解怎么思考！"""

    def generate_example_response(self, message, style):
        """例题展示"""
        return """很好！看例题是学习数学的好方法。

**例题：求二次函数的最值**

题目：求函数 y = -x² + 4x - 3 的最大值

解法：
1. 识别参数：a=-1, b=4, c=-3
2. 因为a<0，开口向下，有最大值
3. 顶点x坐标：x = -4/(2×(-1)) = 2
4. 顶点y坐标：y = -(2)² + 4×2 - 3 = -4 + 8 - 3 = 1
5. 最大值是1，在x=2时取得

**你学会了吗？**
类似的题目你可以试试：求 y = 2x² - 8x + 5 的最小值"""

    def generate_general_response(self, message, style):
        """通用回复"""
        responses = [
            """这是个好问题！让我们一起来思考：

**我的建议：**
1. 先理解问题的本质
2. 回忆相关的知识点
3. 尝试用不同角度分析

你能告诉我更多关于这个问题的背景吗？""",
            """我理解你的问题！数学学习需要耐心和练习。

**学习技巧：**
- 把复杂问题分解成小步骤
- 用图表帮助理解
- 多做类似题目巩固

具体是什么地方让你困惑呢？""",
            """很好的学习态度！让我来帮助你：

**思考过程：**
1. 确定问题类型
2. 选择合适的方法
3. 逐步解决问题

你现在学到哪一部分了？有什么具体困难吗？"""
        ]
        return random.choice(responses)


def run_server(port=8080):
    """启动HTTP服务器"""
    server_address = ('', port)
    httpd = HTTPServer(server_address, EducationAPIHandler)

    print(f"🚀 REST API服务器启动成功")
    print(f"📍 监听端口: {port}")
    print(f"🌐 访问地址: http://localhost:{port}")
    print(f"📊 API文档: http://localhost:{port}/health")
    print()
    print("✅ 服务器已就绪，等待请求...")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print()

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("🛑 服务器已停止")
        print()
        httpd.server_close()


if __name__ == "__main__":
    run_server(8080)
