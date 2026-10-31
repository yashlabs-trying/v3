package asciitable

import (
	"strings"
	"testing"
)

func dfLines(s string) []string { return strings.Split(strings.TrimRight(s, "\n"), "\n") }

func dfContainsLine(s, want string) bool {
	for _, l := range dfLines(s) {
		if strings.TrimRight(l, " ") == want {
			return true
		}
	}
	return false
}

func dfCount(s, sub string) int { return strings.Count(s, sub) }

func TestDataForgeTeleportTruncation(t *testing.T) {
	t.Run("truncate.format", func(t *testing.T) {
		table := MakeTable([]string{"Name"})
		table.AddColumn(Column{Title: "Motto", MaxCellLength: 25, FootnoteLabel: "[*]"})
		table.AddColumn(Column{Title: "Age", MaxCellLength: 2})
		table.AddFootnote("[*]", "note-here")
		table.AddRow([]string{"Joe", "Trains are much better than cars", "40"})
		out := table.AsBuffer().String()
		if !strings.Contains(out, "Trains are much better th... [*]") {
			t.Errorf("want truncated cell with label; got:\n%s", out)
		}
		table2 := MakeTable([]string{"A"})
		table2.AddColumn(Column{Title: "B", MaxCellLength: 2})
		table2.AddRow([]string{"x", "for ever and ever"})
		out2 := table2.AsBuffer().String()
		if !strings.Contains(out2, "fo...") {
			t.Errorf("want 'fo...' for limit 2 no label; got:\n%s", out2)
		}
		if strings.Contains(out2, "[*]") {
			t.Errorf("no-label column must not emit a footnote label; got:\n%s", out2)
		}
	})

	t.Run("truncate.boundary", func(t *testing.T) {
		table := MakeTable([]string{"A"})
		table.AddColumn(Column{Title: "B", MaxCellLength: 3})
		table.AddColumn(Column{Title: "C", MaxCellLength: 0})
		table.AddRow([]string{"abc", "abc", "abcdefgh"})
		out := table.AsBuffer().String()
		if strings.Contains(out, "...") {
			t.Errorf("cells within limit and unbounded column must not be truncated; got:\n%s", out)
		}
		if !strings.Contains(out, "abcdefgh") {
			t.Errorf("unbounded column must show full cell; got:\n%s", out)
		}
	})

	t.Run("width.from_rendered", func(t *testing.T) {
		table := MakeTable([]string{"N"})
		table.AddColumn(Column{Title: "M", MaxCellLength: 4})
		table.AddRow([]string{"Joe", "abcdefgh"})
		out := table.AsBuffer().String()
		if !strings.Contains(out, "abcd...") {
			t.Errorf("want 'abcd...' rendered; got:\n%s", out)
		}
	})

	t.Run("footnote.section", func(t *testing.T) {
		table := MakeTable([]string{"N"})
		table.AddColumn(Column{Title: "M1", MaxCellLength: 3, FootnoteLabel: "[*]"})
		table.AddColumn(Column{Title: "M2", MaxCellLength: 3, FootnoteLabel: "[*]"})
		table.AddColumn(Column{Title: "M3", MaxCellLength: 3, FootnoteLabel: "[**]"})
		table.AddFootnote("[*]", "shared-note")
		table.AddFootnote("[**]", "unused-note")
		table.AddRow([]string{"a", "abcdef", "abcdef"})
		out := table.AsBuffer().String()
		if dfCount(out, "[*] shared-note") != 1 {
			t.Errorf("shared label must be emitted once; got:\n%s", out)
		}
		if strings.Contains(out, "unused-note") {
			t.Errorf("unreferenced footnote must not appear; got:\n%s", out)
		}
		if !strings.Contains(out, "\n\n[*] shared-note") {
			t.Errorf("footnote section must be preceded by a blank line; got:\n%q", out)
		}
	})

	t.Run("headless.extra_values", func(t *testing.T) {
		table := MakeHeadlessTable(2)
		table.AddRow([]string{"1", "2", "3"})
		out := table.AsBuffer().String()
		if strings.Contains(out, "3") {
			t.Errorf("extra values must be dropped; got:\n%s", out)
		}
	})
}
