# Contributing to Emergency News Summarizer

First off, thank you for considering contributing to Emergency News Summarizer! It's people like you that make this tool valuable for the amateur radio and emergency management communities.

## 🎯 Ways to Contribute

### 1. Report Bugs
Found a bug? Please create an issue with:
- Clear description of the problem
- Steps to reproduce
- Expected vs actual behavior
- Python version and OS
- Error messages or logs

### 2. Suggest Features
Have an idea? Create an issue with:
- Clear description of the feature
- Use case (how it helps radio ops/emergency comms)
- Example of how it would work

### 3. Improve Documentation
- Fix typos or clarify instructions
- Add examples or use cases
- Create guides for specific radio modes
- Translate to other languages

### 4. Write Code
- Fix bugs
- Implement new features
- Improve performance
- Add tests

---

## 🚀 Getting Started

### Fork and Clone

1. Fork the repository on GitHub
2. Clone your fork:
```bash
git clone https://github.com/yourusername/emergency-news-radio.git
cd emergency-news-radio
```

3. Add upstream remote:
```bash
git remote add upstream https://github.com/originalusername/emergency-news-radio.git
```

### Set Up Development Environment

1. Create a virtual environment:
```bash
python -m venv venv
venv\Scripts\activate  # Windows
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Test the app:
```bash
python news_summarizer.py
```

---

## 📝 Development Guidelines

### Code Style

- Follow [PEP 8](https://pep8.org/) for Python code
- Use meaningful variable names
- Add docstrings to functions and classes
- Comment complex logic

**Example:**
```python
def generate_weather_txt(filename, region_num, forecasts, region_name):
    """
    Generate plain text weather forecast for a FEMA region.
    
    Args:
        filename (str): Output file path
        region_num (int): FEMA region number (1-10)
        forecasts (list): List of forecast dictionaries
        region_name (str): Human-readable region name
    """
    # Implementation here
```

### File Organization

```
emergency-news-radio/
├── news_summarizer.py          # Main GUI application
├── emergency_module.py         # Emergency data fetching
├── plaintext_generators.py     # Text file generators
├── requirements.txt            # Dependencies
├── README.md                   # Main documentation
├── CHANGELOG.md               # Version history
└── docs/                      # Additional documentation
```

### Commit Messages

Use clear, descriptive commit messages:

**Good:**
```
Add selective region selection for weather forecasts
Fix tweet truncation issue in plaintext generator
Update README with new checkbox features
```

**Bad:**
```
Update
Fix bug
Changes
```

### Testing

Before submitting a PR:

1. **Test the GUI** - Verify all features work
2. **Test file generation** - Check all output types
3. **Test selective generation** - Verify checkboxes work
4. **Check file sizes** - Ensure files are still compact
5. **Test on Windows 10 and 11** if possible

---

## 🔄 Pull Request Process

### 1. Create a Branch

```bash
git checkout -b feature/amazing-feature
```

Branch naming:
- `feature/description` - New features
- `bugfix/description` - Bug fixes
- `docs/description` - Documentation
- `refactor/description` - Code refactoring

### 2. Make Your Changes

- Write clear, commented code
- Follow the code style guidelines
- Test thoroughly

### 3. Commit Your Changes

```bash
git add .
git commit -m "Add amazing feature"
```

### 4. Push to Your Fork

```bash
git push origin feature/amazing-feature
```

### 5. Create Pull Request

1. Go to GitHub and create a Pull Request
2. Fill in the PR template:
   - **Description:** What does this PR do?
   - **Motivation:** Why is this change needed?
   - **Testing:** How was it tested?
   - **Related Issues:** Link any related issues

### 6. Respond to Feedback

- Be open to suggestions
- Make requested changes
- Push updates to the same branch

---

## 🎨 Priority Areas for Contribution

### High Priority

1. **MacOS/Linux Support**
   - Port GUI to cross-platform
   - Test on different OS
   - Update installation docs

2. **Additional News Sources**
   - Reuters integration
   - AFP integration
   - Local news sources

3. **International Weather**
   - WMO data integration
   - International cities
   - Metric units option

### Medium Priority

4. **Enhanced Space Weather**
   - Solar wind speed
   - CME predictions
   - Aurora forecasts

5. **Direct Radio Integration**
   - APRS direct send
   - Winlink RMS connector
   - VARA modem support

6. **UI Improvements**
   - Settings persistence
   - Preset configurations
   - Dark mode

### Low Priority (Nice to Have)

7. **Web Interface**
   - Browser-based option
   - Mobile-friendly design

8. **Additional Features**
   - Export to CSV
   - Historical data tracking
   - Comparison reports

---

## 🐛 Bug Fix Guidelines

When fixing a bug:

1. **Reproduce the bug** - Confirm you can replicate it
2. **Identify root cause** - Find the actual problem
3. **Write a fix** - Keep it minimal and focused
4. **Test thoroughly** - Verify the fix works
5. **Check for regressions** - Ensure nothing else broke
6. **Document the fix** - Update CHANGELOG.md

---

## 📚 Documentation Standards

### README Updates

When adding features:
- Update features list
- Add usage examples
- Update file size estimates if changed

### Code Comments

```python
# Good: Explains WHY
# Skip regions that aren't selected to reduce file size
if not self.weather_regions[region_num].get():
    continue

# Bad: Explains WHAT (obvious from code)
# Check if region is selected
if not self.weather_regions[region_num].get():
    continue
```

### Documentation Files

Create separate .md files for major features:
- Clear title and purpose
- Step-by-step instructions
- Examples and use cases
- Screenshots if applicable

---

## 🤝 Community Guidelines

### Be Respectful
- Welcome newcomers
- Be patient with questions
- Provide constructive feedback
- Respect different skill levels

### Be Professional
- Stay on topic
- No spam or self-promotion
- No political or controversial content
- Focus on emergency communications use

### Be Helpful
- Answer questions when you can
- Share your use cases
- Help test new features
- Report bugs you find

---

## 📞 Getting Help

### Questions About Contributing?

- **GitHub Discussions:** Ask in the Q&A section
- **Issues:** Create an issue with the "question" label
- **Documentation:** Check existing docs first

### Need Technical Help?

- **Installation issues:** Check TROUBLESHOOTING.md
- **Feature questions:** Check feature-specific docs
- **Bug reports:** Create a detailed issue

---

## 🎓 Learning Resources

### Python
- [Official Python Tutorial](https://docs.python.org/3/tutorial/)
- [Real Python](https://realpython.com/)

### Tkinter (GUI)
- [TkDocs](https://tkdocs.com/)
- [Python Tkinter Tutorial](https://realpython.com/python-gui-tkinter/)

### APIs
- [Requests Library](https://requests.readthedocs.io/)
- [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)

### Amateur Radio
- [ARRL EmComm](http://www.arrl.org/emergency-communications)
- [Winlink](https://www.winlink.org/)

---

## ✅ Contributor Checklist

Before submitting your PR:

- [ ] Code follows PEP 8 style guidelines
- [ ] All functions have docstrings
- [ ] Complex logic has comments
- [ ] Tested on Windows
- [ ] No API keys or secrets in code
- [ ] CHANGELOG.md updated
- [ ] README.md updated if needed
- [ ] Commit messages are clear
- [ ] PR description is complete

---

## 🏆 Recognition

Contributors will be:
- Listed in README acknowledgments
- Credited in release notes
- Appreciated by the community!

---

## 📄 License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

## 🙏 Thank You!

Your contributions help amateur radio operators and emergency managers worldwide. Every bug fix, feature addition, and documentation improvement makes a difference.

**73 and thanks for contributing!** 📡

---

*Questions about this guide? Open an issue or start a discussion!*
