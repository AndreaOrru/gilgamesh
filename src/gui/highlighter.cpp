#include <QColor>

#include "gui/highlighter.hpp"

#include "gui/constants.hpp"
#include "gui/disassemblyview.hpp"
#include "opcodes.hpp"

Highlighter::Highlighter(QTextDocument* parent) : QSyntaxHighlighter(parent) {
  setupFormats();
  setupPatterns();
}

void Highlighter::setupFormats() {
  argumentAliasFormat.setForeground(Qt::darkRed);

  assertedStateChangeFormat.setBackground(ASSERTION_COLOR);
  assertedStateChangeFormat.setForeground(Qt::white);

  commentFormat.setForeground(Qt::gray);

  completeJumpTableFormat.setBackground(JUMPTABLE_COLOR);
  completeJumpTableFormat.setForeground(Qt::white);

  entryPointFormat.setForeground(ENTRYPOINT_COLOR);
  entryPointFormat.setFontWeight(QFont::Bold);

  labelFormat.setForeground(Qt::darkRed);
  labelFormat.setFontWeight(QFont::Bold);

  localLabelFormat.setForeground(Qt::darkRed);

  opcodeFormat.setForeground(Qt::blue);

  partialJumpTableFormat.setBackground(PARTIAL_JUMPTABLE_COLOR);

  unknownStateChangeFormat.setBackground(UNKNOWN_COLOR);
  unknownStateChangeFormat.setForeground(Qt::white);
}

void Highlighter::setupPatterns() {
  Rule rule;

  rule.pattern = QRegularExpression(" (\\.|!)?[A-Za-z0-9_]+");
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

    case BlockState::CompleteJumpTable:
      setFormat(0, text.size(), completeJumpTableFormat);
      break;

    case BlockState::EntryPointLabel:
      setFormat(0, text.size(), entryPointFormat);
      break;

    case BlockState::PartialJumpTable:
      setFormat(0, text.size(), partialJumpTableFormat);
      break;

    case BlockState::UnknownStateChange:
      setFormat(0, text.size(), unknownStateChangeFormat);
      break;

    default:
      break;
  }
}
