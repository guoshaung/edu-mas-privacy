#!/usr/bin/env python3
"""
打开前端界面的Python脚本
"""
import webbrowser
import os

base_path = "/Users/mac9/.openclaw/workspace/edu-mas-privacy/"

# 学生端
student_url = f"file:///{base_path}/frontend/student.html"
teacher_url = f"file:///{base_path}frontend/teacher.html"

print("🚀 打开前端界面...")
print(f"\n📱 学生端: {student_url}")
print(f"👨‍🏫 教师端: {teacher_url}")
print("\n正在打开浏览器...")

webbrowser.open(student_url)
webbrowser.open(teacher_url)

print("\n✅ 前端界面已在浏览器中打开！")

# 打开其他前端
other_urls = [
    ("赛博朋克版", f"file:///{base_path}frontend/cyberpunk.html"),
    ("暗黑风格", f"file:///{base_path}frontend/dark.html"),
    ("监控面板", f"file:///{base_path}frontend/index.html"),
]

for name, url in other_urls:
    print(f"\n打开{name}: {url}")
    webbrowser.open(url)

print("\n🎉 所有前端界面已打开！")
