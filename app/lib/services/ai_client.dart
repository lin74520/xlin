import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:http/http.dart' as http;
import 'package:path/path.dart' as p;

import 'storage.dart';

class AiClient {
  final String apiKey;
  final String baseUrl;
  final String model;

  AiClient({required this.apiKey, required this.baseUrl, required this.model});

  // 简化为逐章请求（非SSE），在移动端更稳定；本地保存由客户端完成
  Stream<String> generateChapterStream({
    required int startChapter,
    required int chapterWords,
    required int chapterCount,
    required bool untilFinale,
    required String projectId,
  }) async* {
    int generated = 0;
    const maxAuto = 200;
    int chapterNum = startChapter;

    while (true) {
      if (!untilFinale && generated >= chapterCount) break;
      if (untilFinale && generated >= maxAuto) break;

      yield '\n开始生成第$chapterNum 章...\n';

      final outline = await _simpleChat([
        {'role': 'system', 'content': '你是资深网文作者，先给出简洁的章节细纲（不超过5行）。'},
        {'role': 'user', 'content': '请输出本章细纲，要求紧扣主线、冲突明确。'},
      ]);

      final title = await _simpleChat([
        {'role': 'system', 'content': '生成本章标题，10字以内，风格贴合网文。只返回标题文本。'},
        {'role': 'user', 'content': '根据以下细纲生成标题：\n$outline'},
      ]);

      yield '标题：$title\n';

      // 内容分段生成，减少超长响应风险
      final buffer = StringBuffer();
      int remain = chapterWords;
      while (remain > 0) {
        final part = await _simpleChat([
          {'role': 'system', 'content': '以成熟网文风格写作，段落清晰，情节紧凑。'},
          {'role': 'user', 'content': '根据以下细纲生成正文片段，约${remain > 800 ? 800 : remain}字。\n细纲：\n$outline\n已写：\n${buffer.toString().substring(buffer.length > 500 ? buffer.length - 500 : 0)}'},
        ], maxTokens: 1024);
        buffer.write(part);
        yield part;
        remain -= 800;
        if (remain <= 0) break;
      }

      final content = buffer.toString();
      await _saveChapter(projectId: projectId, chapterNum: chapterNum, title: title, content: content);
      yield '\n✅ 第$chapterNum 章完成（${content.length}字）\n';

      // 大结局检测
      if (untilFinale && _isFinale(content, title)) {
        yield '🎉 检测到大结局信号，续写结束。\n';
        break;
      }

      generated += 1;
      chapterNum += 1;
    }
    yield '\n[DONE]\n';
  }

  Future<String> _simpleChat(List<Map<String, String>> messages, {int maxTokens = 512}) async {
    final url = Uri.parse('$baseUrl/chat/completions');
    final headers = {
      'Authorization': 'Bearer $apiKey',
      'Content-Type': 'application/json',
    };
    final body = jsonEncode({
      'model': model,
      'messages': messages,
      'temperature': 0.8,
      'max_tokens': maxTokens,
    });
    final resp = await http.post(url, headers: headers, body: body).timeout(const Duration(seconds: 120));
    if (resp.statusCode != 200) {
      throw Exception('API错误 ${resp.statusCode}: ${resp.body}');
    }
    final data = jsonDecode(utf8.decode(resp.bodyBytes));
    return (data['choices'][0]['message']['content'] as String).trim();
  }

  bool _isFinale(String text, String title) {
    final samples = [title, text.substring(0, text.length > 200 ? 200 : text.length), text.substring(text.length > 200 ? text.length - 200 : 0)];
    const kws = ['终章', '大结局', '全书完', '完结', 'THE END'];
    for (final s in samples) {
      for (final k in kws) {
        if (s.contains(k)) return true;
      }
    }
    return false;
  }

  Future<void> _saveChapter({required String projectId, required int chapterNum, required String title, required String content}) async {
    final dir = await Storage.ensureProjectDir(projectId);
    final safe = _sanitize('第${chapterNum.toString().padLeft(3, '0')}章 $title');
    final file = File(p.join(dir.path, '$safe.txt'));
    await file.writeAsString('# 第$chapterNum 章：$title\n\n$content\n\n---\n字数：${content.length}\n生成时间：${DateTime.now()}');

    // 更新完整版
    final full = File(p.join(dir.path, '$projectId（完整版）.txt'));
    final buf = StringBuffer();
    buf.writeln('《$projectId》\n');
    buf.writeln('=' * 50 + '\n');
    final files = dir
        .listSync()
        .whereType<File>()
        .where((f) => f.path.endsWith('.txt') && !p.basename(f.path).contains('（完整版）'))
        .toList()
      ..sort((a, b) => p.basename(a.path).compareTo(p.basename(b.path)));
    for (final f in files) {
      final t = await f.readAsString();
      buf.writeln(t);
      buf.writeln('\n' + '=' * 50 + '\n');
    }
    await full.writeAsString(buf.toString());
  }

  String _sanitize(String name) {
    const illegal = '<>:"/\\|?*';
    final filtered = name.split('').where((c) => !illegal.contains(c)).join().trim();
    return filtered.isEmpty ? '未命名' : filtered;
  }
}


