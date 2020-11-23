#pragma once

#include <QDialog>
#include <optional>
#include <utility>

#include "jumptable.hpp"
#include "types.hpp"

class QCheckBox;
class QLineEdit;

class EditJumpTableDialog : public QDialog {
  Q_OBJECT

 public:
  EditJumpTableDialog(const JumpTable* jumpTable, QWidget* parent = nullptr);

  std::optional<std::pair<u16, u16>> range;
  JumpTableStatus status;

 private slots:
  void accept();

 private:
  void restoreFromJumpTable(const JumpTable* jumpTable);
  auto createTextAreas();
  auto createButtonBox();
  auto createCheckBox();
  void setupLayout();

  QLineEdit* startText;
  QLineEdit* endText;
  QCheckBox* completeCheckBox;
};
