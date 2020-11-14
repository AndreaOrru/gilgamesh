#include "gui/highlighter.hpp"

#include "opcodes.hpp"

Highlighter::Highlighter(QTextDocument* parent) : QSyntaxHighlighter(parent) {
  setupFormats();
  setupPatterns();
}

void Highlighter::setupFormats() {
  commentFormat.setForeground(Qt::gray);

  labelFormat.setForeground(Qt::darkRed);
  labelFormat.setFontWeight(QFont::Bold);

  opcodeFormat.setForeground(Qt::darkBlue);
}

void Highlighter::setupPatterns() {
  Rule rule;

  QStringList opcode_patterns;
  for (auto& op : OPCODE_NAMES) {
    auto pattern = QString::fromStdString("\\b" + op + "\\b");
    rule.pattern = QRegularExpression(pattern);
    rule.format = opcodeFormat;
    rules.append(rule);
  }

  rule.pattern = QRegularExpression("^[A-Za-z0-9_]+:");
  rule.format = labelFormat;
  rules.append(rule);

  rule.pattern = QRegularExpression(";[^\n]*");
  rule.format = commentFormat;
  rules.append(rule);
}

void Highlighter::highlightBlock(const QString& text) {
  for (auto& rule : rules) {
    auto match_iterator = rule.pattern.globalMatch(text);
    while (match_iterator.hasNext()) {
      auto match = match_iterator.next();
      setFormat(match.capturedStart(), match.capturedLength(), rule.format);
    }
  }
}
