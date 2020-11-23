#include <QBoxLayout>
#include <QCheckBox>
#include <QDialogButtonBox>
#include <QLabel>
#include <QLineEdit>
#include <QValidator>

#include "analysis.hpp"
#include "editjumptabledialog.hpp"

using namespace std;

EditJumpTableDialog::EditJumpTableDialog(const JumpTable* jumpTable,
                                         QWidget* parent)
    : QDialog(parent) {
  setWindowTitle("Edit Jump Table");
  setupLayout();

  restoreFromJumpTable(jumpTable);
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

auto EditJumpTableDialog::createCheckBox() {
  completeCheckBox = new QCheckBox("Complete", this);
  return completeCheckBox;
}

void EditJumpTableDialog::setupLayout() {
  auto vbox = new QVBoxLayout(this);
  vbox->addLayout(createTextAreas());
  vbox->addWidget(createCheckBox());
  vbox->addWidget(createButtonBox());
}

void EditJumpTableDialog::restoreFromJumpTable(const JumpTable* jumpTable) {
  range = jumpTable->range();
  if (range.has_value()) {
    startText->setText(QString::number(range->first));
    endText->setText(QString::number(range->second));
  }

  completeCheckBox->setChecked(jumpTable->status == JumpTableStatus::Complete);
}

void EditJumpTableDialog::accept() {
  bool ok = true;
  auto start = startText->text().toInt(&ok);
  auto end = endText->text().toInt(&ok);

  if (ok) {
    range = {start, end};
    status = completeCheckBox->isChecked() ? JumpTableStatus::Complete
                                           : JumpTableStatus::Partial;
  } else {
    range = nullopt;
  }

  QDialog::accept();
}
