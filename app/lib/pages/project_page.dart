import 'dart:convert';
import 'dart:io';

import 'package:archive/archive_io.dart';
import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:path/path.dart' as p;
import 'package:shared_preferences/shared_preferences.dart';

import '../services/ai_client.dart';
import '../services/storage.dart';

class ProjectPage extends StatefulWidget {
  final String projectId;
  const ProjectPage({super.key, required this.projectId});

  @override
  State<ProjectPage> createState() => _ProjectPageState();
}

class _ProjectPageState extends State<ProjectPage> {
  final List<FileSystemEntity> _chapters = [];
  String _log = '';
  bool _untilFinale = false;
  int _chapterWords = 3000;
  int _chapterCount = 1;

  @override
  void initState() {
    super.initState();
    _refreshChapters();
  }

  Future<Directory> _projDir() async => await Storage.ensureProjectDir(widget.projectId);

  Future<void> _refreshChapters() async {
    final dir = await _projDir();
    final list = dir
        .listSync()
        .whereType<File>()
        .where((f) => f.path.endsWith('.txt') && !p.basename(f.path).contains('（完整版）'))
        .toList()
      ..sort((a, b) => p.basename(a.path).compareTo(p.basename(b.path)));
    setState(() {
      _chapters
        ..clear()
        ..addAll(list);
    });
  }

  Future<void> _importTxt() async {
    final result = await FilePicker.platform.pickFiles(type: FileType.custom, allowedExtensions: ['txt']);
    if (result == null || result.files.single.path == null) return;
    final dir = await _projDir();
    final file = File(result.files.single.path!);
    final target = File(p.join(dir.path, p.basename(file.path)));
    await file.copy(target.path);
    await _refreshChapters();
    if (mounted) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('已导入TXT')));
  }

  Future<void> _importFolderZip() async {
    final result = await FilePicker.platform.pickFiles(allowMultiple: true, type: FileType.custom, allowedExtensions: ['txt']);
    if (result == null || result.files.isEmpty) return;
    final dir = await _projDir();
    for (final f in result.files) {
      if (f.path == null) continue;
      final src = File(f.path!);
      if (!src.path.toLowerCase().endsWith('.txt')) continue;
      await src.copy(p.join(dir.path, p.basename(src.path)));
    }
    await _refreshChapters();
    if (mounted) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('已导入文件夹TXT')));
  }

  Future<void> _continue() async {
    final prefs = await SharedPreferences.getInstance();
    final apiKey = prefs.getString('api_key') ?? '';
    final apiBase = prefs.getString('api_base') ?? '';
    final model = prefs.getString('model') ?? '';
    if (apiKey.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('请先在首页保存API Key')));
      return;
    }

    final startChapter = _chapters.length + 1;
    setState(() => _log = '');
    final client = AiClient(apiKey: apiKey, baseUrl: apiBase, model: model);
    await for (final chunk in client.generateChapterStream(
      startChapter: startChapter,
      chapterWords: _chapterWords,
      chapterCount: _untilFinale ? 1 << 30 : _chapterCount,
      untilFinale: _untilFinale,
      projectId: widget.projectId,
    )) {
      setState(() => _log += chunk);
    }
    await _refreshChapters();
  }

  Future<void> _clearAll() async {
    final ok = await showDialog<bool>(
      context: context,
      builder: (_) => AlertDialog(
        title: const Text('确认'),
        content: const Text('清空所有章节并删除本地文件？'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('取消')),
          FilledButton(onPressed: () => Navigator.pop(context, true), child: const Text('清空')),
        ],
      ),
    );
    if (ok != true) return;
    final dir = await _projDir();
    for (final f in dir.listSync()) {
      try { f.deleteSync(recursive: true); } catch (_) {}
    }
    await _refreshChapters();
    if (mounted) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('已清空')));
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('项目：${widget.projectId}')),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.all(12),
            child: Row(
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(children: [
                        const Text('每章字数'),
                        const SizedBox(width: 8),
                        DropdownButton<int>(
                          value: _chapterWords,
                          items: const [1000, 2000, 3000, 4000, 5000]
                              .map((e) => DropdownMenuItem(value: e, child: Text('$e')))
                              .toList(),
                          onChanged: (v) => setState(() => _chapterWords = v ?? 3000),
                        ),
                        const SizedBox(width: 16),
                        const Text('续写章节数'),
                        const SizedBox(width: 8),
                        DropdownButton<int>(
                          value: _chapterCount,
                          items: const [1, 2, 3, 5, 10]
                              .map((e) => DropdownMenuItem(value: e, child: Text('$e')))
                              .toList(),
                          onChanged: (v) => setState(() => _chapterCount = v ?? 1),
                        ),
                      ]),
                      Row(children: [
                        Checkbox(value: _untilFinale, onChanged: (v) => setState(() => _untilFinale = v ?? false)),
                        const Text('直到大结局（检测“终章/大结局/全书完/完结/THE END”）')
                      ])
                    ],
                  ),
                ),
                Column(children: [
                  FilledButton(onPressed: _continue, child: const Text('开始续写')),
                  const SizedBox(height: 8),
                  OutlinedButton(onPressed: _clearAll, child: const Text('清空全部')),
                ])
              ],
            ),
          ),
          const Divider(height: 1),
          Expanded(
            child: Row(
              children: [
                Expanded(
                  flex: 2,
                  child: Column(
                    children: [
                      Padding(
                        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                        child: Row(
                          children: [
                            FilledButton.tonal(onPressed: _importTxt, child: const Text('导入TXT')),
                            const SizedBox(width: 8),
                            FilledButton.tonal(onPressed: _importFolderZip, child: const Text('导入文件夹TXT')),
                          ],
                        ),
                      ),
                      Expanded(
                        child: ListView.builder(
                          itemCount: _chapters.length,
                          itemBuilder: (_, i) {
                            final f = _chapters[i] as File;
                            return ListTile(
                              title: Text(p.basename(f.path)),
                              onTap: () async {
                                final text = await File(f.path).readAsString();
                                if (!context.mounted) return;
                                showDialog(
                                  context: context,
                                  builder: (_) => AlertDialog(
                                    title: Text(p.basename(f.path)),
                                    content: SingleChildScrollView(child: Text(text.length > 1000 ? '${text.substring(0, 1000)}...' : text)),
                                  ),
                                );
                              },
                            );
                          },
                        ),
                      ),
                    ],
                  ),
                ),
                const VerticalDivider(width: 1),
                Expanded(
                  flex: 3,
                  child: SingleChildScrollView(
                    padding: const EdgeInsets.all(12),
                    child: Text(_log.isEmpty ? '续写日志将实时显示...' : _log),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}


