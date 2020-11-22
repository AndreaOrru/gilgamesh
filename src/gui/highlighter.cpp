#include "gui/highlighter.hpp"
#include <QColor>

#include "gui/disassemblyview.hpp"

#include "opcodes.hpp"

Highlighter::Highlighter(QTextDocument* parent) : QSyntaxHighlighter(parent) {
  setupFormats();
  setupPatterns();
}

void Highlighter::setupFormats() {
  argumentAliasFormat.setForeground(Qt::darkRed);

  assertedStateChangeFormat.setBackground(QColor("mediumpurple"));
  assertedStateChangeFormat.setForeground(Qt::white);

  commentFormat.setForeground(Qt::gray);

  labelFormat.setForeground(Qt::darkRed);
  labelFormat.setFontWeight(QFont::Bold);

  localLabelFormat.setForeground(Qt::darkRed);

  opcodeFormat.setForeground(Qt::blue);

  unknownStateChangeFormat.setBackground(QColor("orangered"));
  unknownStateChangeFormat.setForeground(Qt::white);
}

void Highlighter::setupPatterns() {
  Rule rule;

  rule.pattern = QRegularExpression(" \\.?[A-Za-z0-9_]+");
  rule.format = argumentAliasFormat;
  rules.append(rule);

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

  rule.pattern = QRegularExpression("^\\.[A-Za-z0-9_]+:");
  rule.format = localLabelFormat;
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

  switch (currentBlockState()) {
    case BlockState::AssertedStateChange:
      setFormat(0, text.size(), assertedStateChangeFormat);
      break;

    case BlockState::UnknownStateChange:
      setFormat(0, text.size(), unknownStateChangeFormat);
      break;

    default:
      break;
  }
}
