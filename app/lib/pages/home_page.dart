import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../services/storage.dart';
import '../pages/project_page.dart';

class HomePage extends StatefulWidget {
  const HomePage({super.key});

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  late final TextEditingController _apiKey;
  late final TextEditingController _apiBase;
  late final TextEditingController _model;
  String _provider = 'OpenAI';

  String? _projectId;

  @override
  void initState() {
    super.initState();
    _apiKey = TextEditingController();
    _apiBase = TextEditingController(text: 'https://api.openai.com/v1');
    _model = TextEditingController(text: 'gpt-4o-mini');
    _load();
  }

  Future<void> _load() async {
    final prefs = await SharedPreferences.getInstance();
    _apiKey.text = prefs.getString('api_key') ?? '';
    _apiBase.text = prefs.getString('api_base') ?? _apiBase.text;
    _model.text = prefs.getString('model') ?? _model.text;
    setState(() {});
  }

  Future<void> _save() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('api_key', _apiKey.text.trim());
    await prefs.setString('api_base', _apiBase.text.trim());
    await prefs.setString('model', _model.text.trim());
    await prefs.setString('provider', _provider);
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('设置已保存')),
      );
    }
  }

  void _applyPreset(String provider) {
    setState(() {
      _provider = provider;
      switch (provider) {
        case 'DeepSeek':
          _apiBase.text = 'https://api.deepseek.com/v1';
          _model.text = 'deepseek-chat';
          break;
        case 'OpenAI':
          _apiBase.text = 'https://api.openai.com/v1';
          _model.text = 'gpt-4o-mini';
          break;
        case 'Moonshot':
          _apiBase.text = 'https://api.moonshot.cn/v1';
          _model.text = 'moonshot-v1-8k';
          break;
        case 'Zhipu':
          _apiBase.text = 'https://open.bigmodel.cn/api/paas/v4';
          _model.text = 'glm-4';
          break;
        case 'Qwen':
          _apiBase.text = 'https://dashscope.aliyuncs.com/compatible-mode/v1';
          _model.text = 'qwen-turbo';
          break;
        default:
          // Custom - keep user values
          break;
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('小林AI小说 (手机端)')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          const Text('服务商预设', style: TextStyle(fontWeight: FontWeight.bold)),
          const SizedBox(height: 8),
          Row(children: [
            DropdownButton<String>(
              value: _provider,
              items: const [
                'OpenAI','DeepSeek','Moonshot','Zhipu','Qwen','Custom'
              ].map((e) => DropdownMenuItem(value: e, child: Text(e))).toList(),
              onChanged: (v) => _applyPreset(v ?? 'Custom'),
            ),
            const SizedBox(width: 8),
            const Text('选择后会填充 API Base 与 Model（可手动改）')
          ]),
          const SizedBox(height: 12),
          const Text('模型设置', style: TextStyle(fontWeight: FontWeight.bold)),
          const SizedBox(height: 8),
          TextField(
            controller: _apiKey,
            obscureText: true,
            decoration: const InputDecoration(labelText: 'API Key (用户自行填写)', border: OutlineInputBorder()),
          ),
          const SizedBox(height: 8),
          TextField(
            controller: _apiBase,
            decoration: const InputDecoration(labelText: 'API Base (OpenAI兼容)', border: OutlineInputBorder()),
          ),
          const SizedBox(height: 8),
          TextField(
            controller: _model,
            decoration: const InputDecoration(labelText: 'Model', border: OutlineInputBorder()),
          ),
          const SizedBox(height: 8),
          ElevatedButton(onPressed: _save, child: const Text('保存设置')),
          const Divider(height: 32),

          const Text('项目', style: TextStyle(fontWeight: FontWeight.bold)),
          const SizedBox(height: 8),
          TextField(
            onChanged: (v) => _projectId = v.trim(),
            decoration: const InputDecoration(
              labelText: '项目名（小说名）',
              hintText: '例如：稳健世子苟成帝',
              border: OutlineInputBorder(),
            ),
          ),
          const SizedBox(height: 8),
          ElevatedButton(
            onPressed: () async {
              if ((_projectId ?? '').isEmpty) {
                ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('请填写项目名')));
                return;
              }
              Navigator.of(context).push(MaterialPageRoute(
                builder: (_) => ProjectPage(projectId: _projectId!.trim()),
              ));
            },
            child: const Text('进入项目'),
          ),
          const SizedBox(height: 16),
          const Text('说明：本App直接连接AI服务，不需要本地/云端后端，导入TXT/ZIP后可续写，支持直到大结局。'),
        ],
      ),
    );
  }
}


