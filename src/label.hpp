#pragma once

#include <QString>
#include <string>

struct Label {
  Label();
  Label(const char* label);
  Label(std::string label);
  Label(QString label);
  Label(std::string subroutineLabel, std::string localLabel);

  std::string asArgument() const;
  std::string combinedLabel() const;
  operator std::string() const;
  operator QString() const;
  const char* c_str() const;

  std::string subroutineLabel;
  std::string localLabel;
};
