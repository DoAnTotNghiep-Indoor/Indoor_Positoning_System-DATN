import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import 'theme/app_theme.dart';
import 'widgets/app_bottom_nav.dart';
import 'screens/home_screen.dart';
import 'screens/map_screen.dart';
import 'screens/search_screen.dart';
import 'screens/settings_screen.dart';

void main() {
  SystemChrome.setSystemUIOverlayStyle(const SystemUiOverlayStyle(
    statusBarColor: Colors.transparent,
    statusBarIconBrightness: Brightness.dark,
  ));
  runApp(const IpsDluApp());
}

class IpsDluApp extends StatelessWidget {
  const IpsDluApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'IPS DLU',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.light,
      home: const AppShell(),
    );
  }
}

/// Khung chính: giữ bottom nav cố định, đổi nội dung theo tab.
class AppShell extends StatefulWidget {
  const AppShell({super.key});

  @override
  State<AppShell> createState() => _AppShellState();
}

class _AppShellState extends State<AppShell> {
  int _index = 0;
  bool _searching = false;

  @override
  Widget build(BuildContext context) {
    final body = _searching
        ? const SearchScreen()
        : switch (_index) {
            0 => const HomeScreen(),
            1 => const MapScreen(),
            _ => const SettingsScreen(),
          };

    return Scaffold(
      extendBody: true,
      body: Stack(
        children: [
          Positioned.fill(child: body),
          Align(
            alignment: Alignment.bottomCenter,
            child: AppBottomNav(
              currentIndex: _index,
              searchActive: _searching,
              onTap: (i) => setState(() {
                _index = i;
                _searching = false;
              }),
              onSearchTap: () => setState(() => _searching = !_searching),
            ),
          ),
        ],
      ),
    );
  }
}
