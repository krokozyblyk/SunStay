param([Parameter(Mandatory=$true)][string]$Path)
$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
try {
    $doc = $word.Documents.Open($Path, $false, $false)
    $seen = @{}
    foreach ($p in $doc.Paragraphs) {
        $n = $p.Range.Style.NameLocal
        if (-not $seen.ContainsKey($n)) { $seen[$n] = $p.Range.Text.Trim().Substring(0,[Math]::Min(40,$p.Range.Text.Trim().Length)) }
    }
    foreach ($k in $seen.Keys) { Write-Output "$k => $($seen[$k])" }
    Write-Output "TOCCOUNT=$($doc.TablesOfContents.Count)"
    $doc.Close($false)
} finally { $word.Quit() }
