param(
  [Parameter(Mandatory=$true)][string]$TaskRoot,
  [Parameter(Mandatory=$true)][string]$InputDocx,
  [Parameter(Mandatory=$true)][string]$OutputPdf
)
$ErrorActionPreference='Stop'
$rootPath=(Resolve-Path -LiteralPath $TaskRoot).Path.TrimEnd('\')+'\'
$sourcePath=(Resolve-Path -LiteralPath $InputDocx).Path
$pdfPath=[IO.Path]::GetFullPath($OutputPdf)
if (-not $sourcePath.StartsWith($rootPath,[StringComparison]::OrdinalIgnoreCase)) { throw 'Input outside task' }
if (-not $pdfPath.StartsWith($rootPath,[StringComparison]::OrdinalIgnoreCase)) { throw 'Output outside task' }
if ([IO.Path]::GetExtension($pdfPath) -ne '.pdf') { throw 'Output must be PDF' }
if (Test-Path -LiteralPath $pdfPath) { throw 'Use a fresh render directory; existing PDF will not be overwritten' }
[IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($pdfPath)) | Out-Null
$app=$null
$document=$null
try {
  $app=New-Object -ComObject Word.Application
  $app.Visible=$false
  $app.DisplayAlerts=0
  $document=$app.Documents.Open($sourcePath,$false,$true,$false)
  $document.Repaginate()
  $pageCount=$document.ComputeStatistics(2)
  $protection=$document.ProtectionType
  $document.ExportAsFixedFormat($pdfPath,17)
  [PSCustomObject]@{opened=$true;pages=$pageCount;protectionType=$protection;pdf=$pdfPath} | ConvertTo-Json
} finally {
  if ($null -ne $document) { $document.Close(0);[void][Runtime.InteropServices.Marshal]::ReleaseComObject($document) }
  if ($null -ne $app) { $app.Quit();[void][Runtime.InteropServices.Marshal]::ReleaseComObject($app) }
}
