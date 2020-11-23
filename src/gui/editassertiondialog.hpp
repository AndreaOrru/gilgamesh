#pragma once

#include <QDialog>
#include <optional>

#include "assertion.hpp"

class QGroupBox;
class QRadioButton;

class EditAssertionDialog : public QDialog {
  Q_OBJECT

 public:
  EditAssertionDialog(std::optional<Assertion> assertion,
                      QWidget* parent = nullptr);

  std::optional<Assertion> assertion;

 private slots:
  void accept();

 private:
  auto createRadioButtons();
  auto createButtonBox();
  void setupLayout();

  void applyToAssertion();
  void restoreFromAssertion();
  void applyDisabledState();

  QGroupBox* createAssertionTypeGroup();
  QGroupBox* createRegisterAssertionGroup(QString reg);
  QRadioButton* createRadioButton(QString title, QGroupBox* group);

  QGroupBox* assertionTypeGroup;
  QRadioButton* assertionTypeNone;
  QRadioButton* assertionTypeInstruction;
  QRadioButton* assertionTypeSubroutine;

  QGroupBox* mAssertionGroup;
  QRadioButton* mAssertionNone;
  QRadioButton* mAssertionZero;
  QRadioButton* mAssertionOne;

  QGroupBox* xAssertionGroup;
  QRadioButton* xAssertionNone;
  QRadioButton* xAssertionZero;
  QRadioButton* xAssertionOne;
};
