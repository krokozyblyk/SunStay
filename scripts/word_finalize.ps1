param([Parameter(Mandatory=$true)][string]$Path)

$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
try {
    $doc = $word.Documents.Open($Path, $false, $false)
    $doc.ActiveWindow.View.Type = 3

    # --- Title page: single spacing, no first-line indent, so it fits exactly one page
    $tocStart = -1
    for ($i = 1; $i -le $doc.Paragraphs.Count; $i++) {
        $t = $doc.Paragraphs.Item($i).Range.Text.Trim()
        if ($t -eq "СОДЕРЖАНИЕ") { $tocStart = $i; break }
    }
    if ($tocStart -gt 0) {
        for ($i = 1; $i -lt $tocStart; $i++) {
            $p = $doc.Paragraphs.Item($i)
            $p.Range.ParagraphFormat.LineSpacingRule = 0   # wdLineSpaceSingle
            $p.Range.ParagraphFormat.FirstLineIndent = 0
            $p.Range.ParagraphFormat.SpaceAfter = 0
            $p.Range.ParagraphFormat.SpaceBefore = 0
        }
    }

    # --- Replace placeholder TOC with a real Word TOC (plain, correct page numbers)
    if ($tocStart -gt 0) {
        $find = $doc.Content
        $find.Find.Text = "Обновите поле (F9), чтобы построить содержание."
        $find.Find.Execute()
        if ($find.Find.Found) {
            $range = $find.Duplicate
            $range.Text = ""
            $null = $doc.TablesOfContents.Add($range, $false, 1, 3, $true, "", $true, "", "", "", "", $false)
        }
        foreach ($toc in $doc.TablesOfContents) { $toc.Update() | Out-Null }
    }

    $doc.Fields.Update() | Out-Null
    $doc.Repaginate()
    $doc.Save()
    Write-Output "WORD OK pages=$($doc.ComputeStatistics(2))"

    $doc.Close($false)
} finally {
    $word.Quit()
}
