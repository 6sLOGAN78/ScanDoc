package styles

import (
	"github.com/charmbracelet/lipgloss"
)

var (
	// Premium Native Terminal Palette
	// Restrained, terminal-compatible colors
	BgColor         = lipgloss.Color("0")   // Default terminal bg
	PrimaryText     = lipgloss.Color("252") // Soft white
	SecondaryText   = lipgloss.Color("245") // Gray
	MutedText       = lipgloss.Color("240") // Dim gray
	SelectionBg     = lipgloss.Color("236") // Subtle background highlight
	ActiveBorder    = lipgloss.Color("245")
	InactiveBorder  = lipgloss.Color("237")

	// Semantic colors
	AccentColor     = lipgloss.Color("110") // Muted blue
	SuccessColor    = lipgloss.Color("114") // Muted green
	WarningColor    = lipgloss.Color("179") // Muted yellow
	ErrorColor      = lipgloss.Color("167") // Muted red
	InfoColor       = lipgloss.Color("109") // Muted cyan

	// Typography & Hierarchy
	TitleStyle = lipgloss.NewStyle().
			Bold(true).
			Foreground(PrimaryText)

	SectionStyle = lipgloss.NewStyle().
			Foreground(AccentColor).
			Bold(true)

	PrimaryStyle = lipgloss.NewStyle().
			Foreground(PrimaryText)

	SecondaryStyle = lipgloss.NewStyle().
			Foreground(SecondaryText)

	MutedStyle = lipgloss.NewStyle().
			Foreground(MutedText)

	// Layout and Panels
	// Sidebar uses a subtle right border
	SidebarStyle = lipgloss.NewStyle().
			Border(lipgloss.NormalBorder(), false, true, false, false).
			BorderForeground(InactiveBorder).
			PaddingRight(1).
			PaddingLeft(1)

	SidebarFocusedStyle = lipgloss.NewStyle().
			Border(lipgloss.NormalBorder(), false, true, false, false).
			BorderForeground(ActiveBorder).
			PaddingRight(1).
			PaddingLeft(1)

	MainContentStyle = lipgloss.NewStyle().
			PaddingLeft(2)

	// Lists and Selections
	// Selection is a subtle background, not neon
	SelectedItemStyle = lipgloss.NewStyle().
			Foreground(PrimaryText).
			Background(SelectionBg).
			PaddingLeft(1).
			PaddingRight(1).
			Bold(true)

	NormalItemStyle = lipgloss.NewStyle().
			Foreground(SecondaryText).
			PaddingLeft(1)

	// Breadcrumbs / Header
	HeaderStyle = lipgloss.NewStyle().
			Foreground(SecondaryText).
			PaddingBottom(1)

	// Command Bar / Footer
	FooterStyle = lipgloss.NewStyle().
			Foreground(MutedText).
			PaddingTop(1)

	// Badges
	BadgeSuccess = lipgloss.NewStyle().Foreground(SuccessColor)
	BadgeWarning = lipgloss.NewStyle().Foreground(WarningColor)
	BadgeError   = lipgloss.NewStyle().Foreground(ErrorColor)
	BadgeInfo    = lipgloss.NewStyle().Foreground(InfoColor)
	BadgeAccent  = lipgloss.NewStyle().Foreground(AccentColor)

	// Tables
	TableHeaderStyle = lipgloss.NewStyle().
			Foreground(MutedText).
			Bold(false).
			Underline(true)

	TableRowStyle = lipgloss.NewStyle().
			Foreground(PrimaryText)
			
	// Migration aliases
	ActiveItemStyle = SelectedItemStyle
	PanelStyle = lipgloss.NewStyle()
	SeparatorStyle = lipgloss.NewStyle().Foreground(MutedText)
)
