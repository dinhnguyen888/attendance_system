import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/auth_provider.dart';
import '../constants/app_colors.dart';
import '../widgets/custom_button.dart';
import '../widgets/custom_text_field.dart';

class LoginView extends StatefulWidget {
  const LoginView({super.key});

  @override
  State<LoginView> createState() => _LoginViewState();
}

class _LoginViewState extends State<LoginView> {
  final _formKey = GlobalKey<FormState>();
  final _usernameController = TextEditingController();
  final _passwordController = TextEditingController();
  bool _obscurePassword = true;

  @override
  void dispose() {
    _usernameController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  Future<void> _login() async {
    if (_formKey.currentState!.validate()) {
      final authProvider = context.read<AuthProvider>();
      final success = await authProvider.login(
        _usernameController.text.trim(),
        _passwordController.text,
      );

      if (success && mounted) {
        Navigator.of(context).pushReplacementNamed('/home');
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24.0),
          child: Form(
            key: _formKey,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                const SizedBox(height: 60),
                _buildHeader(),
                const SizedBox(height: 60),
                _buildLoginForm(),
                const SizedBox(height: 40),
                _buildLoginButton(),
                const SizedBox(height: 20),
                _buildErrorDisplay(),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildHeader() {
    return Column(
      children: [
        Container(
          width: 120,
          height: 120,
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(60),
            boxShadow: [
              BoxShadow(
                color: AppColors.primary.withOpacity(0.3),
                blurRadius: 20,
                offset: const Offset(0, 10),
              ),
            ],
          ),
          child: ClipRRect(
            borderRadius: BorderRadius.circular(60),
            child: Image.asset(
              'assets/images/logoAPP.png',
              width: 120,
              height: 120,
              fit: BoxFit.cover,
            ),
          ),
        ),
        const SizedBox(height: 24),
        const Text(
          'Attendance System',
          style: TextStyle(
            fontSize: 28,
            fontWeight: FontWeight.bold,
            color: AppColors.textPrimary,
          ),
        ),
        const SizedBox(height: 8),
        const Text(
          'Đăng nhập để tiếp tục',
          style: TextStyle(
            fontSize: 16,
            color: AppColors.textSecondary,
          ),
        ),
      ],
    );
  }

  Widget _buildLoginForm() {
    return Column(
      children: [
        CustomTextField(
          controller: _usernameController,
          labelText: 'Tên đăng nhập',
          prefixIcon: Icons.person,
          validator: (value) {
            if (value == null || value.trim().isEmpty) {
              return 'Vui lòng nhập tên đăng nhập';
            }
            return null;
          },
        ),
        const SizedBox(height: 20),
        CustomTextField(
          controller: _passwordController,
          labelText: 'Mật khẩu',
          prefixIcon: Icons.lock,
          obscureText: _obscurePassword,
          suffixIcon: IconButton(
            icon: Icon(
              _obscurePassword ? Icons.visibility : Icons.visibility_off,
              color: AppColors.textSecondary,
            ),
            onPressed: () {
              setState(() {
                _obscurePassword = !_obscurePassword;
              });
            },
          ),
          validator: (value) {
            if (value == null || value.isEmpty) {
              return 'Vui lòng nhập mật khẩu';
            }
            return null;
          },
        ),
      ],
    );
  }

  Widget _buildLoginButton() {
    return Consumer<AuthProvider>(
      builder: (context, authProvider, child) {
        return CustomButton(
          onPressed: authProvider.isLoading ? null : _login,
          text: authProvider.isLoading ? 'Đang đăng nhập...' : 'Đăng nhập',
          isLoading: authProvider.isLoading,
        );
      },
    );
  }

  Widget _buildErrorDisplay() {
    return Consumer<AuthProvider>(
      builder: (context, authProvider, child) {
        if (authProvider.error == null || authProvider.error!.isEmpty) {
          return const SizedBox.shrink();
        }

        return Container(
          margin: const EdgeInsets.only(top: 16),
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(
            color: Colors.red.shade50,
            borderRadius: BorderRadius.circular(8),
            border: Border.all(color: Colors.red.shade200),
          ),
          child: Row(
            children: [
              Icon(
                Icons.error_outline,
                color: Colors.red.shade600,
                size: 20,
              ),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  authProvider.error!,
                  style: TextStyle(
                    color: Colors.red.shade700,
                    fontSize: 14,
                  ),
                ),
              ),
              IconButton(
                icon: Icon(
                  Icons.close,
                  color: Colors.red.shade600,
                  size: 18,
                ),
                onPressed: () => authProvider.clearError(),
                padding: EdgeInsets.zero,
                constraints: const BoxConstraints(
                  minWidth: 24,
                  minHeight: 24,
                ),
              ),
            ],
          ),
        );
      },
    );
  }
}
