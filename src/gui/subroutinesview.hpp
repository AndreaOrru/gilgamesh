#pragma once

#include <QListWidget>

class Analysis;

class SubroutinesView : public QListWidget {
  Q_OBJECT

 public:
  SubroutinesView(QWidget* parent = nullptr);

 public slots:
  void renderAnalysis(const Analysis* analysis);
};
