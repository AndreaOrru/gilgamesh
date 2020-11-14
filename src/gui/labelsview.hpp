#pragma once

#include <QListWidget>

class LabelsView : public QListWidget {
  Q_OBJECT

 public:
  LabelsView(QWidget* parent = nullptr);

 public slots:
  void setLabels(QStringList labels);
};
