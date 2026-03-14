/**
 * 前端API客户端
 * 连接到后端gRPC服务
 */

// API配置
const API_CONFIG = {
    gatewayUrl: 'http://localhost:50051',
    educationUrl: 'http://localhost:50052',
    // 如果你有REST API包装器，使用这个
    restApiUrl: 'http://localhost:8080/api'
};

/**
 * 学生消息发送API
 */
async function sendStudentMessage(studentData) {
    try {
        const response = await fetch(`${API_CONFIG.restApiUrl}/student/message`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                student_id: studentData.studentId || 'stu_001',
                message: studentData.message,
                learning_style: studentData.learningStyle || 'Visual',
                timestamp: new Date().toISOString()
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        return {
            success: true,
            response: data.response,
            metadata: data.metadata
        };
    } catch (error) {
        console.error('发送消息失败:', error);
        return {
            success: false,
            error: error.message,
            // 失败时返回备用响应
            response: generateFallbackResponse(studentData.learningStyle || 'Visual')
        };
    }
}

/**
 * 教师端获取学生数据API
 */
async function getStudentData(studentId) {
    try {
        const response = await fetch(`${API_CONFIG.restApiUrl}/teacher/student/${studentId}`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            }
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error('获取学生数据失败:', error);
        return null;
    }
}

/**
 * 教师端获取所有学生列表API
 */
async function getAllStudents() {
    try {
        const response = await fetch(`${API_CONFIG.restApiUrl}/teacher/students`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            }
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error('获取学生列表失败:', error);
        // 返回模拟数据
        return getMockStudents();
    }
}

/**
 * 教师端生成测试API
 */
async function generateTest(studentId, knowledgePoint) {
    try {
        const response = await fetch(`${API_CONFIG.restApiUrl}/teacher/generate-test`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                student_id: studentId,
                knowledge_point: knowledgePoint
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error('生成测试失败:', error);
        return {
            success: false,
            questions: [],
            error: error.message
        };
    }
}

/**
 * 备用响应生成器（当后端不可用时）
 */
function generateFallbackResponse(learningStyle) {
    const responses = {
        'Visual': [
            '试着画个图来理解这个概念会更容易！',
            '我们可以用图像法来学习这个公式',
            '观察图像的变化趋势，能发现什么规律？'
        ],
        'Aural': [
            '我给你详细讲解一遍这个知识点',
            '试着把你理解的思路讲给我听听',
            '我们可以口头讨论一下这个概念'
        ],
        'ReadWrite': [
            '把这个概念写成笔记会更好理解',
            '我们列个提纲总结关键点',
            '建议你阅读教材上的相关章节'
        ],
        'Kinesthetic': [
            '让我们动手实践一下！',
            '可以用实物模型来帮助理解',
            '做个小实验验证一下'
        ]
    };

    const styleResponses = responses[learningStyle] || responses['Visual'];
    return styleResponses[Math.floor(Math.random() * styleResponses.length)];
}

/**
 * 模拟学生数据（当后端不可用时使用）
 */
function getMockStudents() {
    return [
        {
            id: 'stu_001',
            name: '张同学',
            grade: 9,
            style: 'Visual',
            progress: 85,
            weak_points: ['最值应用', '综合题'],
            last_active: '2分钟前'
        },
        {
            id: 'stu_002',
            name: '李同学',
            grade: 9,
            style: 'Aural',
            progress: 72,
            weak_points: ['概念理解', '公式记忆'],
            last_active: '5分钟前'
        },
        {
            id: 'stu_003',
            name: '王同学',
            grade: 10,
            style: 'Kinesthetic',
            progress: 68,
            weak_points: ['基础计算', '几何证明'],
            last_active: '10分钟前'
        },
        {
            id: 'stu_004',
            name: '赵同学',
            grade: 11,
            style: 'ReadWrite',
            progress: 91,
            weak_points: [],
            last_active: '1小时前'
        }
    ];
}

/**
 * 检查后端服务是否可用
 */
async function checkBackendHealth() {
    try {
        const response = await fetch(`${API_CONFIG.restApiUrl}/health`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        return response.ok;
    } catch (error) {
        console.warn('后端服务不可用，使用离线模式');
        return false;
    }
}
