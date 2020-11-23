#pragma once

#include <QDialog>
#include <utility>

#include "types.hpp"

class QLineEdit;

class EditJumpTableDialog : public QDialog {
  Q_OBJECT

 public:
  EditJumpTableDialog(QWidget* parent = nullptr);
  std::pair<u16, u16> range;

 private slots:
  void accept();

 private:
  auto createTextAreas();
  auto createButtonBox();
  void setupLayout();

  QLineEdit* startText;
  QLineEdit* endText;
};
