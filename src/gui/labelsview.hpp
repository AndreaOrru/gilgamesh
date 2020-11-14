#pragma once

#include <QListWidget>

class Analysis;

class LabelsView : public QListWidget {
  Q_OBJECT

 public:
  LabelsView(QWidget* parent = nullptr);

 public slots:
  void setAnalysis(const Analysis* analysis);
};
