# iOS 模拟器支持（Swift Package Manager）

杰理 SDK 随附的 6 个 XCFramework 只有真机二进制。SwiftPM 在编译 Swift 源码前就会选择平台切片，因此仅用 `#if targetEnvironment(simulator)` 包住 SDK 调用，仍会报 `no library for this platform was found`。

插件为每个 XCFramework 增加了仅用于链接的 `arm64` 模拟器占位 framework，支持 Apple silicon Mac 上的原生 iOS 模拟器，不支持 Intel Mac 的 `x86_64` 模拟器。占位 framework 与真机切片保持相同的封装和链接类型：`DFUnits` 为静态 framework，其余 5 个为动态 framework。同一个 XCFramework 不能混放 `.framework` 和裸 `.a` 切片。

这些占位 framework 不包含杰理 SDK 功能。模拟器编译时，插件会跳过真机 SDK 的 Swift、Objective-C 实现和头文件，只注册占位的 MethodChannel 与 EventChannel。真机继续使用原有 SDK 和实现。

模拟器返回空闲状态和空设备列表；蓝牙、OTA 等 SDK 操作返回 `SIMULATOR_UNSUPPORTED`。设备扫描、连接、认证和固件升级必须在真机验证。此兼容方案适用于 SwiftPM 接入，CocoaPods 配置保持原状。

## 宿主接入本地修复

如果宿主仍锁定旧的 Git 提交，可先在宿主 `pubspec.yaml` 的 `dependency_overrides` 下添加：

```yaml
dependency_overrides:
  jl_ota:
    path: ../jl_ota
```

保留该配置下的其他依赖，然后通过宿主现有的渠道切换脚本重新生成 overrides 并执行 `fvm flutter pub get`。不要直接修改 `ios/Flutter/ephemeral` 中的包副本。接入已发布的修复提交后，删除本地 path override，更新锁定的 Git 依赖。

## 重新生成占位库

占位库已随插件分发，宿主无需额外生成。维护时在安装 Xcode 的 macOS 上执行：

```bash
python3 tool/ios_simulator/generate.py
```

该命令重新生成模拟器占位 framework，并逐个调用 `xcodebuild -create-xcframework` 验证真机与模拟器切片的组合、生成平台元数据。不构建 Flutter App，也不修改真机 SDK。
