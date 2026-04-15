# TOOLS.md - Local Notes

Skills define _how_ tools work. This file is for _your_ specifics — the stuff that's unique to your setup.

## 技能使用规范

- 安装新skill前必须先审查（使用 skill-vetter 进行安全检查）
- 不安装来路不明的skill

Things like:

- Camera names and locations
- SSH hosts and aliases
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Anything environment-specific

## Examples

```markdown
### Cameras

- living-room → Main area, 180° wide angle
- front-door → Entrance, motion-triggered

### SSH

- home-server → 192.168.1.100, user: admin

### TTS

- Preferred voice: "Nova" (warm, slightly British)
- Default speaker: Kitchen HomePod
```

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without leaking your infrastructure.

---

### Obsidian

- vault: ~/Documents/garytan (Obsidian 1.12+, CLI enabled)
- config: ~/.config/openclaw/config.yaml (knowledge_base.obsidian_path)
- Inbox 路径: ~/Documents/garytan/宇先生/Inbox/ （不在 vault 根目录）

Add whatever helps you do your job. This is your cheat sheet.
