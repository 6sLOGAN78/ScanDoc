package styles

import (
	"github.com/charmbracelet/lipgloss"
)

var (
	// Theme Colors
	PrimaryColor    = lipgloss.Color("#7D56F4") // Purple Accent
	SecondaryColor  = lipgloss.Color("#22C55E") // Online Green
	WarningColor    = lipgloss.Color("#F59E0B") // Amber Warning
	ErrorColor      = lipgloss.Color("#EF4444") // Red Error
	MutedColor      = lipgloss.Color("#6B7280") // Grey Muted
	BgDark          = lipgloss.Color("#111827") // Dark Container
	TextHighlight   = lipgloss.Color("#38BDF8") // Sky Blue Highlight

	// Layout & Container Styles
	HeaderStyle = lipgloss.NewStyle().
			Bold(true).
			Foreground(lipgloss.Color("#FFFFFF")).
			Background(PrimaryColor).
			Padding(0, 1).
			MarginBottom(1)

	FooterStyle = lipgloss.NewStyle().
			Foreground(MutedColor).
			Padding(0, 1).
			MarginTop(1)

	PanelStyle = lipgloss.NewStyle().
			Border(lipgloss.RoundedBorder()).
			BorderForeground(PrimaryColor).
			Padding(1, 2)

	ActiveItemStyle = lipgloss.NewStyle().
			Bold(true).
			Foreground(TextHighlight).
			PaddingLeft(1)

	NormalItemStyle = lipgloss.NewStyle().
			Foreground(lipgloss.Color("#E5E7EB")).
			PaddingLeft(3)

	BadgeGreen = lipgloss.NewStyle().
			Bold(true).
			Foreground(lipgloss.Color("#FFFFFF")).
			Background(SecondaryColor).
			Padding(0, 1)

	BadgeAmber = lipgloss.NewStyle().
			Bold(true).
			Foreground(lipgloss.Color("#FFFFFF")).
			Background(WarningColor).
			Padding(0, 1)

	LogBoxStyle = lipgloss.NewStyle().
			Border(lipgloss.NormalBorder()).
			BorderForeground(MutedColor).
			Padding(0, 1).
			Height(6)
)
