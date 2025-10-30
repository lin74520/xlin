"""
小说生成引擎
"""
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class Chapter:
    """章节数据类"""
    number: int
    title: str
    content: str
    outline: str
    word_count: int
    status: str  # 'pending', 'generating', 'completed', 'failed'
    created_at: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'number': self.number,
            'title': self.title,
            'content': self.content,
            'outline': self.outline,
            'word_count': self.word_count,
            'status': self.status,
            'created_at': self.created_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Chapter':
        return cls(**data)


class NovelGenerator:
    """小说生成器"""
    
    def __init__(self, provider):
        self.provider = provider
        self.chapters: List[Chapter] = []
        self.novel_context = {
            'title': '',
            'style': '',
            'genre': '',
            'inspiration': '',
            'characters': [],
            'plot_points': [],
            'corpus': []
        }
    
    def set_context(self, **kwargs):
        """设置小说上下文"""
        self.novel_context.update(kwargs)
    
    def generate_outline(self, total_words: int, chapter_words: int) -> str:
        """生成小说大纲"""
        total_chapters = max(1, total_words // chapter_words)
        
        system_prompt = """你是一位经验丰富的小说大纲策划师。请根据用户提供的信息，创建一个详细的小说大纲。
大纲应该包括：
1. 小说名称（简洁有力，3-8字）
2. 故事核心冲突
3. 主要角色设定
4. 情节发展脉络
5. 关键转折点
6. 结局方向

请确保大纲逻辑连贯，情节紧凑，有足够的张力和吸引力。"""
        
        user_prompt = f"""请为以下小说创建大纲：

风格：{self.novel_context.get('style', '自然细腻')}
题材：{self.novel_context.get('genre', '现实')}
预计章节数：{total_chapters}章
每章字数：{chapter_words}字
灵感：{self.novel_context.get('inspiration', '无')}

请生成一个完整的小说大纲，必须以"### 《小说名》小说大纲"开头。"""
        
        messages = [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_prompt}
        ]
        
        try:
            outline = self.provider.generate(messages, temperature=0.9, max_tokens=2000)
            # 提取小说名称
            self._extract_novel_title(outline)
            return outline
        except Exception as e:
            raise Exception(f"生成大纲失败: {str(e)}")
    
    def _extract_novel_title(self, outline: str):
        """从大纲中提取小说名称"""
        import re
        # 匹配 ### 《XXX》小说大纲 格式
        match = re.search(r'###\s*《(.+?)》', outline)
        if match:
            title = match.group(1).strip()
            self.novel_context['title'] = title
        else:
            # 如果没找到，使用默认名称
            self.novel_context['title'] = '未命名小说'
    
    def generate_chapter_outline(self, chapter_num: int, previous_chapters: List[Chapter]) -> str:
        """生成章节细纲"""
        system_prompt = """你是一位小说章节策划师。请根据已有内容和整体大纲，为下一章创建详细的章节细纲。
细纲应包括：
1. 本章核心冲突
2. 情节推进要点
3. 角色发展
4. 新增伏笔或解决旧伏笔
5. 本章结尾钩子"""
        
        # 构建上下文
        context = f"""小说信息：
风格：{self.novel_context.get('style')}
题材：{self.novel_context.get('genre')}
整体大纲：{self.novel_context.get('outline', '无')}

"""
        
        # 添加前几章摘要
        if previous_chapters:
            context += "前面章节摘要：\n"
            for ch in previous_chapters[-3:]:  # 只取最近3章
                context += f"第{ch.number}章：{ch.outline[:200]}\n"
        
        context += f"\n请为第{chapter_num}章创建详细的章节细纲。"
        
        messages = [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': context}
        ]
        
        try:
            outline = self.provider.generate(messages, temperature=0.8, max_tokens=800)
            return outline
        except Exception as e:
            raise Exception(f"生成章节细纲失败: {str(e)}")
    
    def generate_chapter_title(self, chapter_num: int, chapter_outline: str, **params) -> str:
        """生成章节标题"""
        genre = params.get('genre', self.novel_context.get('genre', '现实'))
        
        messages = [
            {'role': 'system', 'content': f'你是一个专业的{genre}小说标题创作大师，擅长创作简洁有力、富有吸引力的章节标题。你的标题总能抓住读者眼球，让人忍不住想点开阅读。'},
            {'role': 'user', 'content': f"""请为第{chapter_num}章创作一个精彩的标题。

章节细纲：
{chapter_outline}

标题创作要求：
1. 长度：5-12字为佳，最多不超过15字
2. 内容：提炼本章最核心的冲突、转折或高潮点
3. 风格：符合{genre}题材特点，有悬念感和吸引力
4. 技巧：可使用对比、悬念、情感冲击等手法
5. 格式：只输出标题本身，不要引号、序号等其他内容

参考风格：
- 冲突型：《生死抉择》《背叛与真相》
- 悬念型：《消失的线索》《意外来客》
- 情感型：《重逢》《告别过去》
- 转折型：《真相大白》《命运转折》

现在请创作标题："""}
        ]
        
        try:
            title = self.provider.generate(messages, temperature=0.95, max_tokens=50)
            # 清理标题（去除引号、书名号等）
            title = title.strip().strip('《》""\'\'「」『』【】')
            # 如果标题太长，截断
            if len(title) > 15:
                title = title[:15]
            return title if title else f"第{chapter_num}章"
        except Exception as e:
            return f"第{chapter_num}章"  # 失败时返回默认标题
    
    def generate_chapter_content(self, chapter_num: int, chapter_outline: str,
                                 target_words: int, previous_chapters: List[Chapter],
                                 mode: str = 'auto', callback=None, **params) -> str:
        """生成章节内容
        
        Args:
            callback: 回调函数，用于实时更新内容 callback(text)
        """
        # 根据模式决定生成策略
        if mode == 'auto':
            mode = 'multi' if target_words >= 1800 else 'single'
        
        if mode == 'single':
            return self._generate_single_round(chapter_num, chapter_outline, 
                                               target_words, previous_chapters, callback, **params)
        else:
            return self._generate_multi_round(chapter_num, chapter_outline,
                                              target_words, previous_chapters, callback, **params)
    
    def _generate_single_round(self, chapter_num: int, chapter_outline: str,
                               target_words: int, previous_chapters: List[Chapter],
                               callback, **params) -> str:
        """单轮生成"""
        system_prompt = self._build_system_prompt(**params)
        user_prompt = self._build_chapter_prompt(chapter_num, chapter_outline,
                                                 target_words, previous_chapters, **params)
        
        messages = [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_prompt}
        ]
        
        try:
            if callback:
                # 使用流式生成
                content = ""
                for chunk in self.provider.generate_stream(
                    messages,
                    temperature=params.get('temperature', 0.8),
                    max_tokens=params.get('max_tokens', 4096),
                    frequency_penalty=params.get('frequency_penalty', 0.3),
                    presence_penalty=params.get('presence_penalty', 0.0)
                ):
                    content += chunk
                    callback(content)  # 实时回调
                return content
            else:
                # 普通生成
                content = self.provider.generate(
                    messages,
                    temperature=params.get('temperature', 0.8),
                    max_tokens=params.get('max_tokens', 4096),
                    frequency_penalty=params.get('frequency_penalty', 0.3),
                    presence_penalty=params.get('presence_penalty', 0.0)
                )
                return content
        except Exception as e:
            raise Exception(f"生成章节内容失败: {str(e)}")
    
    def _generate_multi_round(self, chapter_num: int, chapter_outline: str,
                              target_words: int, previous_chapters: List[Chapter],
                              callback, **params) -> str:
        """多轮生成"""
        rounds = 2 if target_words < 3000 else 3
        words_per_round = target_words // rounds
        
        full_content = ""
        
        for round_num in range(rounds):
            system_prompt = self._build_system_prompt(**params)
            
            if round_num == 0:
                # 第一轮：开头
                user_prompt = self._build_chapter_prompt(
                    chapter_num, chapter_outline, words_per_round,
                    previous_chapters, part="开头", **params
                )
            elif round_num == rounds - 1:
                # 最后一轮：结尾
                user_prompt = f"""继续第{chapter_num}章的内容，这是本章的结尾部分。

已生成内容：
{full_content[-500:]}

章节细纲：{chapter_outline}

请写出本章结尾部分（约{words_per_round}字），要有适当的收束和悬念。"""
            else:
                # 中间轮：发展
                user_prompt = f"""继续第{chapter_num}章的内容。

已生成内容：
{full_content[-500:]}

章节细纲：{chapter_outline}

请继续写作（约{words_per_round}字），推进情节发展。"""
            
            messages = [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt}
            ]
            
            try:
                if callback:
                    # 使用流式生成
                    round_content = ""
                    for chunk in self.provider.generate_stream(
                        messages,
                        temperature=params.get('temperature', 0.8),
                        max_tokens=params.get('max_tokens', 4096),
                        frequency_penalty=params.get('frequency_penalty', 0.3),
                        presence_penalty=params.get('presence_penalty', 0.0)
                    ):
                        round_content += chunk
                        callback(full_content + round_content)  # 实时回调完整内容
                    full_content += round_content + "\n\n"
                else:
                    # 普通生成
                    content = self.provider.generate(
                        messages,
                        temperature=params.get('temperature', 0.8),
                        max_tokens=params.get('max_tokens', 4096),
                        frequency_penalty=params.get('frequency_penalty', 0.3),
                        presence_penalty=params.get('presence_penalty', 0.0)
                    )
                    full_content += content + "\n\n"
            except Exception as e:
                raise Exception(f"生成章节内容失败（第{round_num+1}轮）: {str(e)}")
        
        return full_content.strip()
    
    def _build_system_prompt(self, **params) -> str:
        """构建系统提示词"""
        style = params.get('style', self.novel_context.get('style', '自然细腻'))
        genre = params.get('genre', self.novel_context.get('genre', '现实'))
        perspective = params.get('perspective', '第三人称')
        
        prompt = f"""你是一位专业的小说作家。

写作要求：
1. 文风：{style}
2. 题材：{genre}
3. 视角：{perspective}
4. 注重细节描写和情感刻画
5. 保持情节连贯性和逻辑性
6. 适当运用对话推进情节
7. 营造适当的氛围和张力

段落格式要求（重要）：
1. 每个段落50-200字为宜，不要写成大段密集文字
2. 对话单独成段，不要和叙述混在一起
3. 场景转换时用空行分隔
4. 段落之间要有明显的呼吸感
5. 避免连续多个短句堆砌

示例格式：
晨雾还没散尽，林北就让人抬着往祠堂去。软轿吱呀作响，八个护卫个个没精打采。路上遇见二房的三公子，对方故意让随从撞了下轿杆。

"哎哟，堂弟这是要去祖宗跟前哭诉？"三公子摇着折扇，"也是，你这身子骨啊，确实该求祖宗保佑。"

林北垂着头没应声，手指在袖中轻轻一弹。三公子腰间的玉佩突然裂了道缝，但他浑然不觉，还在那哈哈大笑。

请严格按照要求创作，确保内容质量和阅读舒适度。"""
        
        # 添加语料库参考
        if self.novel_context.get('corpus'):
            prompt += f"\n\n参考文风示例：\n{self.novel_context['corpus'][0][:200]}"
        
        return prompt
    
    def _build_chapter_prompt(self, chapter_num: int, chapter_outline: str,
                             target_words: int, previous_chapters: List[Chapter],
                             part: str = "完整", **params) -> str:
        """构建章节生成提示词"""
        prompt = f"""请创作第{chapter_num}章的{part}内容。

章节细纲：
{chapter_outline}

目标字数：约{target_words}字

"""
        
        # 添加前文摘要
        if previous_chapters:
            prompt += "前文摘要：\n"
            for ch in previous_chapters[-2:]:
                prompt += f"第{ch.number}章：{ch.content[:300]}...\n\n"
        
        # 添加特殊要求
        opening = params.get('opening', '默认')
        if chapter_num == 1 and opening != '默认':
            prompt += f"\n开局方式：{opening}\n"
        
        pace = params.get('pace', '正常')
        prompt += f"叙事节奏：{pace}\n"
        
        if params.get('grand_finale', False) and chapter_num > len(previous_chapters) * 0.9:
            prompt += "\n注意：这是接近结尾的章节，请开始收束情节线索。\n"
        
        prompt += "\n请开始创作："
        
        return prompt
    
    def format_paragraphs(self, content: str) -> str:
        """格式化段落 - 符合小说阅读习惯"""
        # 移除多余空行和首尾空白
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        
        # 重新组织段落
        formatted = []
        current_paragraph = []
        
        for line in lines:
            # 检查是否是章节标题（跳过）
            if line.startswith('第') and ('章' in line or '节' in line):
                if current_paragraph:
                    formatted.append(''.join(current_paragraph))
                    current_paragraph = []
                continue
            
            # 对话单独成段
            if (line.startswith('"') or line.startswith('"') or 
                line.startswith('「') or line.startswith('"')):
                if current_paragraph:
                    formatted.append(''.join(current_paragraph))
                    current_paragraph = []
                formatted.append(line)
            # 场景转换标记（如空行、分隔符等）
            elif line in ['***', '---', '…', '......']:
                if current_paragraph:
                    formatted.append(''.join(current_paragraph))
                    current_paragraph = []
                formatted.append('\n' + line + '\n')
            # 普通叙述段落
            else:
                # 每个自然段落独立（不合并）
                # 段落长度控制在50-200字之间比较舒适
                if len(line) >= 50:
                    if current_paragraph:
                        formatted.append(''.join(current_paragraph))
                        current_paragraph = []
                    formatted.append(line)
                else:
                    # 短句可以合并，但不超过200字
                    if current_paragraph and len(''.join(current_paragraph)) + len(line) > 200:
                        formatted.append(''.join(current_paragraph))
                        current_paragraph = [line]
                    else:
                        current_paragraph.append(line)
        
        # 处理最后的段落
        if current_paragraph:
            formatted.append(''.join(current_paragraph))
        
        # 用双换行符连接，形成明显的段落间隔
        return '\n\n'.join(formatted)
