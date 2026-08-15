package document

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"scandoc/internal/tui/state"
	"scandoc/internal/tui/styles"
)

type Block struct {
	ID        string `json:"id"`
	BlockType string `json:"block_type"`
	Text      string `json:"text"`
	BBox      struct {
		Left float64 `json:"left"`
		Top  float64 `json:"top"`
	} `json:"bbox"`
}

type Page struct {
	PageIndex int     `json:"page_index"`
	Blocks    []Block `json:"blocks"`
}

type ScandocOutput struct {
	Pages []Page `json:"pages"`
}

func Render(st *state.AppState, selectedIdx int) string {
	var b strings.Builder
	
	if st.ActiveDocumentPath == "" {
		b.WriteString(styles.TitleStyle.Render("Inspector") + "\n\n")
		b.WriteString(styles.MutedStyle.Render("  No document selected.") + "\n")
		b.WriteString("\n" + styles.FooterStyle.Render("Esc Back"))
		return b.String()
	}

	docName := st.ActiveDocumentName
	if docName == "" {
		docName = "document"
	}

	b.WriteString(styles.TitleStyle.Render(fmt.Sprintf("%s / Page %d", docName, st.CurrentPage)) + "\n\n")
	b.WriteString(styles.PrimaryStyle.Render("  Content") + "   " + 
				  styles.MutedStyle.Render("Layout   JSON   Relations") + "\n\n")

	// Load JSON output
	basename := filepath.Base(st.ActiveDocumentPath)
	ext := filepath.Ext(basename)
	jsonName := strings.TrimSuffix(basename, ext) + ".json"
	outDir := filepath.Join(".", "local", "scandoc", "output", basename)
	jsonPath := filepath.Join(outDir, jsonName)

	var output ScandocOutput
	var currentBlocks []Block

	data, err := os.ReadFile(jsonPath)
	if err == nil {
		if err := json.Unmarshal(data, &output); err == nil {
			for _, page := range output.Pages {
				if page.PageIndex == st.CurrentPage-1 {
					currentBlocks = page.Blocks
					break
				}
			}
		}
	}

	if len(currentBlocks) == 0 {
		b.WriteString(styles.MutedStyle.Render("  No extracted content for this page.") + "\n\n")
	} else {
		for i, block := range currentBlocks {
			bboxStr := fmt.Sprintf("%.2f, %.2f", block.BBox.Left, block.BBox.Top)
			if i == selectedIdx {
				b.WriteString(styles.SelectedItemStyle.Render(fmt.Sprintf("> %s", block.BlockType)) + "\n")
				b.WriteString(styles.PrimaryStyle.Render(fmt.Sprintf("  %s", block.Text)) + "\n")
				b.WriteString(styles.MutedStyle.Render(fmt.Sprintf("  ID: %s   Pos: [%s]", block.ID, bboxStr)) + "\n\n")
			} else {
				b.WriteString(styles.SecondaryStyle.Render(fmt.Sprintf("  %s", block.BlockType)) + "\n")
				b.WriteString(styles.MutedStyle.Render(fmt.Sprintf("  %s", block.Text)) + "\n\n")
			}
		}
	}

	sepWidth := st.WindowWidth - 25
	if sepWidth < 10 {
		sepWidth = 50
	}
	
	b.WriteString(styles.MutedStyle.Render(strings.Repeat("─", sepWidth)) + "\n")
	b.WriteString(styles.FooterStyle.Render("↑/↓ Navigate   Tab Switch view   Esc Back"))
	return b.String()
}
