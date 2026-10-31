/*
Copyright 2017 Gravitational, Inc.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
*/

// Package asciitable implements a simple ASCII table formatter for printing
// tabular values into a text terminal.
package asciitable

import (
	"bytes"
	"fmt"
	"strings"
	"text/tabwriter"
)

// Column represents a column in the table. Contains the title of the column,
// the maximum length of a cell, and an optional footnote label that is
// appended to truncated cells.
type Column struct {
	// Title is the column title.
	Title string
	// MaxCellLength is the maximum length of a cell in this column. If a cell
	// is longer than MaxCellLength it is truncated and an ellipsis is added.
	// A value of 0 leaves the column unbounded.
	MaxCellLength int
	// FootnoteLabel is appended to truncated cells and references a footnote
	// registered with AddFootnote.
	FootnoteLabel string
}

// Table holds tabular values in a rows and columns format.
type Table struct {
	columns   []Column
	rows      [][]string
	footnotes map[string]string
}

// MakeTable creates a new instance of the table with given column names.
func MakeTable(headers []string) Table {
	t := MakeHeadlessTable(len(headers))
	for i := range t.columns {
		t.columns[i].Title = headers[i]
	}
	return t
}

// MakeHeadlessTable creates a new instance of the table without any column names.
// The number of columns is required.
func MakeHeadlessTable(columnCount int) Table {
	return Table{
		columns:   make([]Column, columnCount),
		rows:      make([][]string, 0),
		footnotes: make(map[string]string),
	}
}

// AddColumn appends a configured column to the table.
func (t *Table) AddColumn(c Column) {
	t.columns = append(t.columns, c)
}

// AddFootnote associates explanatory text with a footnote label. The note is
// displayed when a truncated cell references the label.
func (t *Table) AddFootnote(label string, note string) {
	if t.footnotes == nil {
		t.footnotes = make(map[string]string)
	}
	t.footnotes[label] = note
}

// AddRow adds a row of cells to the table.
func (t *Table) AddRow(row []string) {
	limit := min(len(row), len(t.columns))
	t.rows = append(t.rows, row[:limit])
}

// AsBuffer returns a *bytes.Buffer with the printed output of the table.
func (t *Table) AsBuffer() *bytes.Buffer {
	var buffer bytes.Buffer

	// Determine the width of each column. A column is as wide as the text
	// finally shown in it, so widths are calculated from the rendered values
	// (which may be truncated and carry an ellipsis and footnote label).
	widths := make([]int, len(t.columns))
	for i, col := range t.columns {
		widths[i] = len(col.Title)
	}

	// Render the cells, truncating those that are too long and keeping track
	// of the footnote labels that are referenced.
	rows := make([][]string, len(t.rows))
	referenced := make(map[string]struct{})
	for r, row := range t.rows {
		rows[r] = make([]string, len(row))
		for c, cell := range row {
			col := t.columns[c]
			if col.MaxCellLength > 0 && len(cell) > col.MaxCellLength {
				cell = cell[:col.MaxCellLength]
				if col.FootnoteLabel != "" {
					cell += " " + col.FootnoteLabel
					referenced[col.FootnoteLabel] = struct{}{}
				}
			}
			rows[r][c] = cell
			widths[c] = max(widths[c], len(cell))
		}
	}

	writer := tabwriter.NewWriter(&buffer, 5, 0, 1, ' ', 0)
	template := strings.Repeat("%v\t", len(t.columns))

	// Header and separator.
	if !t.IsHeadless() {
		var colh []interface{}
		var cols []interface{}

		for i, col := range t.columns {
			colh = append(colh, col.Title)
			cols = append(cols, strings.Repeat("-", widths[i]))
		}
		fmt.Fprintf(writer, template+"\n", colh...)
		fmt.Fprintf(writer, template+"\n", cols...)
	}

	// Body.
	for _, row := range rows {
		var rowi []interface{}
		for _, cell := range row {
			rowi = append(rowi, cell)
		}
		fmt.Fprintf(writer, template+"\n", rowi...)
	}

	writer.Flush()

	// Footnotes. Each referenced label is emitted once, in the order the
	// columns were declared. Labels that are not referenced are not shown.
	// The whole section is separated from the body by a single blank line.
	var footnoteLines []string
	emitted := make(map[string]struct{})
	for _, col := range t.columns {
		label := col.FootnoteLabel
		if label == "" {
			continue
		}
		if _, ok := referenced[label]; !ok {
			continue
		}
		if _, ok := emitted[label]; ok {
			continue
		}
		emitted[label] = struct{}{}
		footnoteLines = append(footnoteLines, fmt.Sprintf("%v %v", label, t.footnotes[label]))
	}
	if len(footnoteLines) > 0 {
		buffer.WriteString("\n")
		for _, line := range footnoteLines {
			buffer.WriteString(line)
			buffer.WriteString("\n")
		}
	}

	return &buffer
}

// IsHeadless returns true if none of the table title cells contains any text.
func (t *Table) IsHeadless() bool {
	total := 0
	for i := range t.columns {
		total += len(t.columns[i].Title)
	}
	return total == 0
}

func min(a, b int) int {
	if a < b {
		return a
	}
	return b
}

func max(a, b int) int {
	if a > b {
		return a
	}
	return b
}
