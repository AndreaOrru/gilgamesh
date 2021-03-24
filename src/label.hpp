#pragma once

#include <QString>
#include <string>

struct Label {
  // Constructors.
  Label();
  Label(const char* label);
  Label(std::string label);
  Label(QString label);
  Label(std::string subroutineLabel, std::string localLabel);

  std::string combinedLabel() const;  // Return the fully qualified label.
  operator std::string() const;       // Return the label as a std::string.
  operator QString() const;           // Return the label as a QString.
  const char* c_str() const;          // Return the label as a C string.
  // Return the label as it would be
  // displayed as an instruction's argument.
  std::string asArgument() const;

  std::string subroutineLabel;
  std::string localLabel;
};
