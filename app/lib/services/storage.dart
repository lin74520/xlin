import 'dart:io';

import 'package:path/path.dart' as p;

class Storage {
  // Android: 使用应用沙盒目录；如需让用户选择目录，可接入 SAF/DocumentFile（后续扩展）
  static Future<Directory> baseDir() async {
    final dir = Directory(p.join(Directory.systemTemp.path, 'ai_novel_mobile'));
    if (!dir.existsSync()) dir.createSync(recursive: true);
    return dir;
  }

  static Future<Directory> ensureProjectDir(String projectId) async {
    final root = await baseDir();
    final dir = Directory(p.join(root.path, projectId));
    if (!dir.existsSync()) dir.createSync(recursive: true);
    return dir;
  }
}


