param([Parameter(Mandatory=$true)][string]$Path)
$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
try {
    $doc = $word.Documents.Open($Path, $false, $false)
    foreach ($toc in $doc.TablesOfContents) { $toc.Update() | Out-Null }
    $doc.Fields.Update() | Out-Null
    $doc.Repaginate()
    $doc.Save()
    Write-Output "UPDATED pages=$($doc.ComputeStatistics(2)) toc=$($doc.TablesOfContents.Count)"
    $doc.Close($false)
} finally {
    $word.Quit()
}
