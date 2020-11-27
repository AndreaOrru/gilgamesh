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

string Label::asArgument() const {
  if (localLabel.empty()) {
    return subroutineLabel;
  } else {
    return "." + localLabel;
  }
}

string Label::combinedLabel() const {
  if (localLabel.empty()) {
    return subroutineLabel;
  } else {
    return subroutineLabel + "." + localLabel;
  }
}

Label::operator string() const {
  if (localLabel.empty()) {
    return subroutineLabel;
  } else {
    return localLabel;
  }
}

Label::operator QString() const {
  return QString::fromStdString(*this);
}

const char* Label::c_str() const {
  if (localLabel.empty()) {
    return subroutineLabel.c_str();
  } else {
    return localLabel.c_str();
  }
}
