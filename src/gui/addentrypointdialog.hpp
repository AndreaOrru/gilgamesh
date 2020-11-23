#pragma once

#include <QDialog>
#include <string>

#include "state.hpp"
#include "types.hpp"

class QGroupBox;
class QLineEdit;
class QRadioButton;

class AddEntryPointDialog : public QDialog {
  Q_OBJECT

 public:
  AddEntryPointDialog(QWidget* parent = nullptr);

  std::string label;
  SubroutinePC pc;
  State state;

 private slots:
  void accept();

 private:
  auto createTextAreas();
  auto createRegisterStateGroup(QString reg);
  auto createButtonBox();
  void setupLayout();

  QLineEdit* labelText;
  QLineEdit* pcText;

  QGroupBox* mStateGroup;
  QRadioButton* mStateZero;
  QRadioButton* mStateOne;

  QGroupBox* xStateGroup;
  QRadioButton* xStateZero;
  QRadioButton* xStateOne;
};
