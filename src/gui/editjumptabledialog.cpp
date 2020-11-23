#include <QBoxLayout>
#include <QDialogButtonBox>
#include <QLabel>
#include <QLineEdit>
#include <QValidator>

#include "editjumptabledialog.hpp"

EditJumpTableDialog::EditJumpTableDialog(QWidget* parent) : QDialog(parent) {
  setWindowTitle("Edit Jump Table");
  setupLayout();
}

auto EditJumpTableDialog::createTextAreas() {
  auto hbox = new QHBoxLayout;

  auto startVbox = new QVBoxLayout;
  auto startLabel = new QLabel("Start:", this);
  startText = new QLineEdit(this);
  startVbox->addWidget(startLabel);
  startVbox->addWidget(startText);

  auto endVbox = new QVBoxLayout;
  auto endLabel = new QLabel("End:", this);
  endText = new QLineEdit(this);
  endVbox->addWidget(endLabel);
  endVbox->addWidget(endText);

  auto validator = new QIntValidator(0x0000, 0xFFFF, this);
  startText->setValidator(validator);
  endText->setValidator(validator);

  hbox->addLayout(startVbox);
  hbox->addLayout(endVbox);

  return hbox;
}

auto EditJumpTableDialog::createButtonBox() {
  auto buttonBox = new QDialogButtonBox(
      QDialogButtonBox::Ok | QDialogButtonBox::Cancel, this);

  connect(buttonBox, &QDialogButtonBox::accepted, this,
          &EditJumpTableDialog::accept);
  connect(buttonBox, &QDialogButtonBox::rejected, this, &QDialog::reject);

  return buttonBox;
}

void EditJumpTableDialog::setupLayout() {
  auto vbox = new QVBoxLayout(this);
  vbox->addLayout(createTextAreas());
  vbox->addWidget(createButtonBox());
}

void EditJumpTableDialog::accept() {
  auto start = startText->text().toInt();
  auto end = endText->text().toInt();
  range = {start, end};

  QDialog::accept();
}
