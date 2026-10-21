param([Parameter(Mandatory=$true)][string]$InputFile,[Parameter(Mandatory=$true)][string]$OutputDir)
$ErrorActionPreference='Stop'
$source=(Resolve-Path -LiteralPath $InputFile).Path
if([IO.Path]::GetExtension($source) -ne '.docx'){throw 'Expected DOCX'}
$out=[IO.Path]::GetFullPath($OutputDir)
if(Test-Path -LiteralPath $out){throw 'Use a new output directory for every render'}
New-Item -ItemType Directory -Path $out | Out-Null
$before=(Get-FileHash -LiteralPath $source).Hash
$word=$null;$doc=$null
try {
 $word=New-Object -ComObject Word.Application
 $word.Visible=$false;$word.DisplayAlerts=0
 $doc=$word.Documents.Open($source,$false,$true,$false)
 $doc.Repaginate();$pages=$doc.ComputeStatistics(2)
 $doc.ExportAsFixedFormat((Join-Path $out 'document.pdf'),17)
 [pscustomobject]@{input=$source;sha256=$before;renderer='Microsoft Word';pages=$pages;visualReview='NOT_RUN';pdf='document.pdf'} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $out 'render.json') -Encoding utf8
} catch {
 [pscustomobject]@{status='FAIL';error=$_.Exception.Message} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $out 'error.json') -Encoding utf8
 throw
} finally {
 if($doc){$doc.Close(0);[void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($doc)}
 if($word){$word.Quit();[void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($word)}
}
if((Get-FileHash -LiteralPath $source).Hash -ne $before){throw 'Read-only source changed'}
Get-Content -LiteralPath (Join-Path $out 'render.json')
