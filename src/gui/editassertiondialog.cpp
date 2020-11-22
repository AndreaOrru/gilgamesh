#include <QBoxLayout>
#include <QDialogButtonBox>
#include <QGroupBox>
#include <QRadioButton>

#include "editassertiondialog.hpp"

using namespace std;

EditAssertionDialog::EditAssertionDialog(Assertion assertion, QWidget* parent)
    : QDialog(parent), assertion{assertion} {
  setWindowTitle("Edit Assertion");
  setupLayout();

  restoreFromAssertion();
}

auto EditAssertionDialog::createRadioButtons() {
  auto hbox = new QHBoxLayout;
  hbox->addWidget(createAssertionTypeGroup());
  hbox->addWidget(createRegisterAssertionGroup("M"));
  hbox->addWidget(createRegisterAssertionGroup("X"));
  return hbox;
}

auto EditAssertionDialog::createButtonBox() {
  auto buttonBox = new QDialogButtonBox(
      QDialogButtonBox::Ok | QDialogButtonBox::Cancel, this);

  connect(buttonBox, &QDialogButtonBox::accepted, this, &QDialog::accept);
  connect(buttonBox, &QDialogButtonBox::rejected, this, &QDialog::reject);

  return buttonBox;
}

void EditAssertionDialog::setupLayout() {
  auto vbox = new QVBoxLayout(this);
  vbox->addLayout(createRadioButtons());
  vbox->addWidget(createButtonBox());
}

QGroupBox* EditAssertionDialog::createAssertionTypeGroup() {
  assertionTypeGroup = new QGroupBox("Type", this);

  assertionTypeNone = createRadioButton("None", assertionTypeGroup);
  assertionTypeInstruction =
      createRadioButton("Instruction", assertionTypeGroup);
  assertionTypeSubroutine = createRadioButton("Subroutine", assertionTypeGroup);

  auto vbox = new QVBoxLayout(assertionTypeGroup);
  vbox->addWidget(assertionTypeNone);
  vbox->addWidget(assertionTypeInstruction);
  vbox->addWidget(assertionTypeSubroutine);

  return assertionTypeGroup;
}

QGroupBox* EditAssertionDialog::createRegisterAssertionGroup(QString reg) {
  QGroupBox** groupBox = (reg == "M") ? &mAssertionGroup : &xAssertionGroup;
  QRadioButton** noneRadio = (reg == "M") ? &mAssertionNone : &xAssertionNone;
  QRadioButton** zeroRadio = (reg == "M") ? &mAssertionZero : &xAssertionZero;
  QRadioButton** oneRadio = (reg == "M") ? &mAssertionOne : &xAssertionOne;

  *groupBox = new QGroupBox(reg, this);
  *noneRadio = createRadioButton("None", *groupBox);
  *zeroRadio = createRadioButton("0", *groupBox);
  *oneRadio = createRadioButton("1", *groupBox);

  auto vbox = new QVBoxLayout(*groupBox);
  vbox->addWidget(*noneRadio);
  vbox->addWidget(*zeroRadio);
  vbox->addWidget(*oneRadio);

  return *groupBox;
}

void EditAssertionDialog::applyToAssertion() {
  applyDisabledState();

  if (assertionTypeNone->isChecked()) {
    assertion.type = AssertionType::None;
    assertion.stateChange = StateChange();
    return;
  } else if (assertionTypeInstruction->isChecked()) {
    assertion.type = AssertionType::Instruction;
  } else if (assertionTypeSubroutine->isChecked()) {
    assertion.type = AssertionType::Subroutine;
  }

  if (mAssertionOne->isChecked()) {
    assertion.stateChange.m = true;
  } else if (mAssertionZero->isChecked()) {
    assertion.stateChange.m = false;
  } else {
    assertion.stateChange.m = nullopt;
  }

  if (xAssertionOne->isChecked()) {
    assertion.stateChange.x = true;
  } else if (xAssertionZero->isChecked()) {
    assertion.stateChange.x = false;
  } else {
    assertion.stateChange.x = nullopt;
  }
}

void EditAssertionDialog::restoreFromAssertion() {
  switch (assertion.type) {
    case AssertionType::None:
      assertionTypeNone->setChecked(true);
      break;
    case AssertionType::Instruction:
      assertionTypeInstruction->setChecked(true);
      break;
    case AssertionType::Subroutine:
      assertionTypeSubroutine->setChecked(true);
      break;
  }

  auto stateChange = assertion.stateChange;
  if (!stateChange.m.has_value()) {
    mAssertionNone->setChecked(true);
  } else if (stateChange.m) {
    mAssertionOne->setChecked(true);
  } else {
    mAssertionZero->setChecked(true);
  }

  if (!stateChange.x.has_value()) {
    xAssertionNone->setChecked(true);
  } else if (stateChange.x) {
    xAssertionOne->setChecked(true);
  } else {
    xAssertionZero->setChecked(true);
  }

  applyDisabledState();
}

void EditAssertionDialog::applyDisabledState() {
  bool disabled = assertionTypeNone->isChecked();
  mAssertionGroup->setDisabled(disabled);
  xAssertionGroup->setDisabled(disabled);
}

QRadioButton* EditAssertionDialog::createRadioButton(QString title,
                                                     QGroupBox* group) {
  auto radioButton = new QRadioButton(title, group);
  connect(radioButton, &QRadioButton::clicked, this,
          &EditAssertionDialog::applyToAssertion);
  return radioButton;
}
