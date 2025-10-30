"""
AI提供商接口实现
支持多个主流AI服务
"""
import json
import time
from typing import Dict, Any, Optional, Generator
import requests
from abc import ABC, abstractmethod

class AIProvider(ABC):
    """AI提供商基类"""
    
    def __init__(self, api_key: str, api_base: str, model: str):
        self.api_key = api_key
        self.api_base = api_base
        self.model = model
    
    @abstractmethod
    def test_connection(self) -> tuple[bool, str]:
        """测试连接"""
        pass
    
    @abstractmethod
    def generate(self, messages: list, temperature: float = 0.8, 
                max_tokens: int = 4096, **kwargs) -> str:
        """生成文本"""
        pass
    
    @abstractmethod
    def generate_stream(self, messages: list, temperature: float = 0.8,
                       max_tokens: int = 4096, **kwargs) -> Generator[str, None, None]:
        """流式生成文本"""
        pass


class OpenAIProvider(AIProvider):
    """OpenAI API提供商"""
    
    def test_connection(self) -> tuple[bool, str]:
        """测试连接"""
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(
                f'{self.api_base}/models',
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                return True, "连接成功！"
            else:
                return False, f"连接失败: {response.status_code} - {response.text}"
        except Exception as e:
            return False, f"连接错误: {str(e)}"
    
    def generate(self, messages: list, temperature: float = 0.8,
                max_tokens: int = 4096, **kwargs) -> str:
        """生成文本"""
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'model': self.model,
                'messages': messages,
                'temperature': temperature,
                'max_tokens': max_tokens,
                **kwargs
            }
            
            response = requests.post(
                f'{self.api_base}/chat/completions',
                headers=headers,
                json=data,
                timeout=120
            )
            
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            else:
                raise Exception(f"API错误: {response.status_code} - {response.text}")
        except Exception as e:
            raise Exception(f"生成失败: {str(e)}")
    
    def generate_stream(self, messages: list, temperature: float = 0.8,
                       max_tokens: int = 4096, **kwargs) -> Generator[str, None, None]:
        """流式生成文本"""
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'model': self.model,
                'messages': messages,
                'temperature': temperature,
                'max_tokens': max_tokens,
                'stream': True,
                **kwargs
            }
            
            response = requests.post(
                f'{self.api_base}/chat/completions',
                headers=headers,
                json=data,
                stream=True,
                timeout=120
            )
            
            if response.status_code != 200:
                raise Exception(f"API错误: {response.status_code}")
            
            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith('data: '):
                        line = line[6:]
                        if line.strip() == '[DONE]':
                            break
                        try:
                            data = json.loads(line)
                            if 'choices' in data and len(data['choices']) > 0:
                                delta = data['choices'][0].get('delta', {})
                                content = delta.get('content', '')
                                if content:
                                    yield content
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            raise Exception(f"流式生成失败: {str(e)}")


class AnthropicProvider(AIProvider):
    """Anthropic Claude API提供商"""
    
    def test_connection(self) -> tuple[bool, str]:
        """测试连接"""
        try:
            headers = {
                'x-api-key': self.api_key,
                'anthropic-version': '2023-06-01',
                'Content-Type': 'application/json'
            }
            
            # 发送一个简单的测试请求
            data = {
                'model': self.model,
                'messages': [{'role': 'user', 'content': 'Hi'}],
                'max_tokens': 10
            }
            
            response = requests.post(
                'https://api.anthropic.com/v1/messages',
                headers=headers,
                json=data,
                timeout=10
            )
            
            if response.status_code == 200:
                return True, "连接成功！"
            else:
                return False, f"连接失败: {response.status_code} - {response.text}"
        except Exception as e:
            return False, f"连接错误: {str(e)}"
    
    def generate(self, messages: list, temperature: float = 0.8,
                max_tokens: int = 4096, **kwargs) -> str:
        """生成文本"""
        try:
            headers = {
                'x-api-key': self.api_key,
                'anthropic-version': '2023-06-01',
                'Content-Type': 'application/json'
            }
            
            # 转换消息格式
            claude_messages = []
            system_message = None
            
            for msg in messages:
                if msg['role'] == 'system':
                    system_message = msg['content']
                else:
                    claude_messages.append({
                        'role': msg['role'],
                        'content': msg['content']
                    })
            
            data = {
                'model': self.model,
                'messages': claude_messages,
                'max_tokens': max_tokens,
                'temperature': temperature
            }
            
            if system_message:
                data['system'] = system_message
            
            response = requests.post(
                'https://api.anthropic.com/v1/messages',
                headers=headers,
                json=data,
                timeout=120
            )
            
            if response.status_code == 200:
                result = response.json()
                return result['content'][0]['text']
            else:
                raise Exception(f"API错误: {response.status_code} - {response.text}")
        except Exception as e:
            raise Exception(f"生成失败: {str(e)}")
    
    def generate_stream(self, messages: list, temperature: float = 0.8,
                       max_tokens: int = 4096, **kwargs) -> Generator[str, None, None]:
        """流式生成文本"""
        try:
            headers = {
                'x-api-key': self.api_key,
                'anthropic-version': '2023-06-01',
                'Content-Type': 'application/json'
            }
            
            # 转换消息格式
            claude_messages = []
            system_message = None
            
            for msg in messages:
                if msg['role'] == 'system':
                    system_message = msg['content']
                else:
                    claude_messages.append({
                        'role': msg['role'],
                        'content': msg['content']
                    })
            
            data = {
                'model': self.model,
                'messages': claude_messages,
                'max_tokens': max_tokens,
                'temperature': temperature,
                'stream': True
            }
            
            if system_message:
                data['system'] = system_message
            
            response = requests.post(
                'https://api.anthropic.com/v1/messages',
                headers=headers,
                json=data,
                stream=True,
                timeout=120
            )
            
            if response.status_code != 200:
                raise Exception(f"API错误: {response.status_code}")
            
            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith('data: '):
                        line = line[6:]
                        try:
                            data = json.loads(line)
                            if data.get('type') == 'content_block_delta':
                                delta = data.get('delta', {})
                                text = delta.get('text', '')
                                if text:
                                    yield text
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            raise Exception(f"流式生成失败: {str(e)}")


def get_provider(provider_name: str, api_key: str, api_base: str, model: str) -> AIProvider:
    """获取AI提供商实例"""
    # OpenAI兼容的提供商
    openai_compatible = ['openai', 'deepseek', 'moonshot', 'zhipu', 'qwen', 'custom']
    
    if provider_name in openai_compatible:
        return OpenAIProvider(api_key, api_base, model)
    elif provider_name == 'anthropic':
        return AnthropicProvider(api_key, api_base, model)
    else:
        raise ValueError(f"不支持的AI提供商: {provider_name}")
