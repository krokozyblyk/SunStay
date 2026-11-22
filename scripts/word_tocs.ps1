param([Parameter(Mandatory=$true)][string]$Path)
$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
try {
    $doc = $word.Documents.Open($Path, $false, $false)

    # appendix titles -> Heading 1 so they appear in the main TOC (keep right alignment)
    foreach ($p in $doc.Paragraphs) {
        $t = $p.Range.Text.Trim()
        if ($t.StartsWith("Приложение ") -and $p.Range.ParagraphFormat.Alignment -eq 2) {
            $p.Range.Style = $doc.Styles.Item("Заголовок 11")
            $p.Range.ParagraphFormat.Alignment = 2
        }
    }

    # collect positions of all СОДЕРЖАНИЕ headings
    $heads = @()
    for ($i = 1; $i -le $doc.Paragraphs.Count; $i++) {
        $t = $doc.Paragraphs.Item($i).Range.Text.Trim()
        if ($t -eq "СОДЕРЖАНИЕ") { $heads += $i }
    }

    # process from the end so earlier indices stay valid
    for ($h = $heads.Count - 1; $h -ge 0; $h--) {
        $idx = $heads[$h]
        $j = $idx + 1
        while ($j -le $doc.Paragraphs.Count) {
            $n = $doc.Paragraphs.Item($j).Range.Style.NameLocal
            if ($n -like "Оглавление*") {
                $doc.Paragraphs.Item($j).Range.Delete() | Out-Null
            } else { break }
        }
        $range = $doc.Paragraphs.Item($idx).Range
        $range.Collapse(0)  # wdCollapseEnd
        $range.InsertParagraphAfter()
        $range.Collapse(0)
        $null = $doc.TablesOfContents.Add($range, $true, 1, 3, $false, "", $true, $true, "", $true, $false, $true)
    }

    foreach ($toc in $doc.TablesOfContents) { $toc.Update() | Out-Null }

    # black, clickable TOC text
    foreach ($nm in @("Оглавление 1", "Оглавление 2", "Оглавление 3")) {
        $st = $doc.Styles.Item($nm)
        $st.Font.Color = 0
        $st.Font.Underline = 0
    }
    $doc.Fields.Update() | Out-Null
    $doc.Repaginate()
    $doc.Save()
    Write-Output "TOCS=$($doc.TablesOfContents.Count) pages=$($doc.ComputeStatistics(2))"
    $doc.Close($false)
} finally { $word.Quit() }
