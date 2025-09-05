# Beacon - Security & Threat Intelligence Feeds

**The ultimate open-source platform for cybersecurity data feeds**

Get structured, real-time data feeds for threat intelligence, security monitoring, and digital asset tracking. Perfect for security teams, researchers, and developers building cybersecurity tools.

## 🚀 Quick Start (60 seconds)

```bash
# 1. Clone and enter directory
git clone https://github.com/Shellomo/Beacon
cd Beacon

# 2. See all available feeds
python job_manager.py list

# 3. Run a feed (e.g., Chrome extensions)
python job_manager.py run --job chrome_extensions_scraper

# 4. Your data is ready!
ls jobs/chrome_extensions/results/
```

**That's it!** 🎉 Your cybersecurity feed data is now available as structured CSV files.

## Available Feeds

| Feed | Description | Output Format | Records |
|------|-------------|---------------|---------|
| **Chrome Extensions** | Chrome Web Store extension metadata, permissions, ratings | CSV | 160K+   |
| **Gitleaks Rules** | Security rules for secret detection | CSV | 200+    |
| **VSCode Extensions** | VS Code Marketplace extension data | CSV | 100K+   |

> **Coming Soon**: 100+ additional feeds including npm packages, WordPress plugins, DLP patterns, IP reputation, and more!

## Use Cases

- **Threat Intelligence**: Monitor malicious extensions, suspicious packages, and security threats
- **Compliance**: Track software inventory, permissions, and security posture  
- **Security Research**: Analyze trends, patterns, and behaviors in digital ecosystems
- **Security Tooling**: Build custom security tools with structured data feeds
- **Market Analysis**: Research software popularity, adoption trends, and competitor analysis

## Features

- **Zero Configuration** - Works out of the box  
- **Structured Data** - Clean CSV/JSON output  
- **Extensible** - Easy to add new feeds  
- **Performance Monitoring** - Built-in execution tracking  
- **Error Handling** - Retry logic and robust error recovery  
- **Open Source** - MIT License, contribute freely  

## 🗺️ Roadmap

### Coming Soon
- **Web UI Dashboard** - Beautiful interface for browsing and downloading feeds
- **API Service** - RESTful API for programmatic access
- **Real-time Updates** - Live feed updates and webhooks
- **Docker Support** - One-click deployment with Docker

### 100+ Planned Feeds

**Packages & Plugins**
- npm packages, PyPI packages, Maven, NuGet
- WordPress plugins, JetBrains plugins  
- Homebrew, Chocolatey, APT packages

**Mobile & Desktop Apps**
- App Store apps, Google Play apps
- Process names, user agents, JA3 fingerprints

**Security & DLP**
- Secret detection patterns, PII regexes
- File type signatures, malware IOCs
- VPN/proxy IP ranges, threat feeds

**Cloud & Infrastructure**  
- AWS/Azure/GCP IP ranges
- CDN endpoints, DNS resolvers
- Certificate transparency logs

[See full roadmap →](FEEDS_ROADMAP.md)

## 🤝 Contributing

**We're building the largest open cybersecurity feed collection!**

### Add a New Feed (5 minutes)

1. **Create directory**: `mkdir jobs/my_feed`
2. **Add config**: Copy template from [jobs/README.md](jobs/README.md)
3. **Write scraper**: Simple Python script that outputs CSV/JSON
4. **Submit PR**: We'll help review and merge!

**Wanted feeds**: Check our [issues](https://github.com/Shellomo/Beacon/issues) for feed requests and bounties! 💰

### Ways to Contribute
- **Add new feeds** - The more data sources, the better!
- **Fix bugs** - Help improve existing feeds
- **Documentation** - Improve guides and examples  
- **Ideas** - Suggest new feed types and use cases

## Documentation

- **[Jobs System](jobs/README.md)** - How to add new feeds

## Support

- **Discussions**: [GitHub Discussions](https://github.com/Shellomo/Beacon/discussions)
- **Bug Reports**: [GitHub Issues](https://github.com/Shellomo/Beacon/issues)

## License

MIT License - See [LICENSE](LICENSE) for details.

---

⭐ **Star this repo if you find it useful!** Help us build the largest open cybersecurity feed platform.

**Keywords**: cybersecurity feeds, threat intelligence, security data, chrome extensions, security research, malware detection, digital forensics, compliance monitoring, security tools, open source security

