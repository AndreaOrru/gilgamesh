#include "label.hpp"

using namespace std;

Label::Label() {}

Label::Label(const char* label) : Label(string(label)) {}

Label::Label(string label) {
  int dotPos = label.find('.');
  if (dotPos == -1) {
    subroutineLabel = label;
  } else {
    subroutineLabel = label.substr(0, dotPos);
    localLabel = label.substr(dotPos + 1, label.size() - dotPos - 1);
  }
}

Label::Label(QString label) : Label(string(label.toStdString())) {}

Label::Label(string subroutineLabel, string localLabel)
    : subroutineLabel{subroutineLabel}, localLabel{localLabel} {}

// Return the full name of the label.
//   If the label is global:
//     globalLabel
//   If the label is local:
//     globalLabel.localLabel
string Label::combinedLabel() const {
  if (localLabel.empty()) {
    return subroutineLabel;
  } else {
    return subroutineLabel + "." + localLabel;
  }
}

// Return the label as a std::string.
//   If the label is global:
//     globalLabel
//   If the label is local:
//     localLabel
Label::operator string() const {
  if (localLabel.empty()) {
    return subroutineLabel;
  } else {
    return localLabel;
  }
}

// Return the label as a QString.
//   If the label is global:
//     globalLabel
//   If the label is local:
//     localLabel
Label::operator QString() const {
  return QString::fromStdString(*this);
}

// Return the label as a C string.
//   If the label is global:
//     globalLabel
//   If the label is local:
//     localLabel
const char* Label::c_str() const {
  if (localLabel.empty()) {
    return subroutineLabel.c_str();
  } else {
    return localLabel.c_str();
  }
}

// Return the name of the label as it would be
// displayed as an argument to an instruction.
string Label::asArgument() const {
  if (localLabel.empty()) {
    return subroutineLabel;
  } else {
    return "." + localLabel;
  }
}
