#include <QBoxLayout>
#include <QDialogButtonBox>
#include <QGroupBox>
#include <QLabel>
#include <QLineEdit>
#include <QRadioButton>

#include "addentrypointdialog.hpp"

AddEntryPointDialog::AddEntryPointDialog(QWidget* parent) : QDialog(parent) {
  setWindowTitle("Add Entry Point");
  setupLayout();
  setFixedSize(sizeHint());
}

auto AddEntryPointDialog::createTextAreas() {
  auto hbox = new QHBoxLayout;

  auto labelVbox = new QVBoxLayout;
  auto labelLabel = new QLabel("Label:", this);
  labelText = new QLineEdit(this);
  labelVbox->addWidget(labelLabel);
  labelVbox->addWidget(labelText);

  auto pcVbox = new QVBoxLayout;
  auto pcLabel = new QLabel("PC:", this);
  pcText = new QLineEdit(this);
  pcVbox->addWidget(pcLabel);
  pcVbox->addWidget(pcText);

  hbox->addLayout(labelVbox);
  hbox->addLayout(pcVbox);

  return hbox;
}

auto AddEntryPointDialog::createRegisterStateGroup(QString reg) {
  QGroupBox** groupBox = (reg == "M") ? &mStateGroup : &xStateGroup;
  QRadioButton** zeroRadio = (reg == "M") ? &mStateZero : &xStateZero;
  QRadioButton** oneRadio = (reg == "M") ? &mStateOne : &xStateOne;

  *groupBox = new QGroupBox(reg, this);
  *zeroRadio = new QRadioButton("0", *groupBox);
  *oneRadio = new QRadioButton("1", *groupBox);

  auto vbox = new QVBoxLayout(*groupBox);
  vbox->addWidget(*zeroRadio);
  vbox->addWidget(*oneRadio);

  (*zeroRadio)->setChecked(true);
  return *groupBox;
}

auto AddEntryPointDialog::createButtonBox() {
  auto buttonBox = new QDialogButtonBox(
      QDialogButtonBox::Ok | QDialogButtonBox::Cancel, this);

  connect(buttonBox, &QDialogButtonBox::accepted, this,
          &AddEntryPointDialog::accept);
  connect(buttonBox, &QDialogButtonBox::rejected, this, &QDialog::reject);

  return buttonBox;
}

void AddEntryPointDialog::setupLayout() {
  auto vbox = new QVBoxLayout(this);
  vbox->addLayout(createTextAreas());

  auto hbox = new QHBoxLayout;
  hbox->addWidget(createRegisterStateGroup("M"));
  hbox->addWidget(createRegisterStateGroup("X"));
  vbox->addLayout(hbox);

  vbox->addWidget(createButtonBox());
}

void AddEntryPointDialog::accept() {
  label = labelText->text().toStdString();
  pc = pcText->text().toInt(nullptr, 16);
  state = State(mStateOne->isChecked(), xStateOne->isChecked());

  QDialog::accept();
}
