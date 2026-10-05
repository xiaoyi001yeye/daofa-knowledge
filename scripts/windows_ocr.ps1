param([Parameter(Mandatory=$true)][string]$ImagePath,
      [Parameter(Mandatory=$true)][string]$OutputPath)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Runtime.WindowsRuntime
$null = [Windows.Storage.StorageFile,Windows.Storage,ContentType=WindowsRuntime]
$null = [Windows.Graphics.Imaging.BitmapDecoder,Windows.Graphics.Imaging,ContentType=WindowsRuntime]
$null = [Windows.Globalization.Language,Windows.Globalization,ContentType=WindowsRuntime]
$null = [Windows.Media.Ocr.OcrEngine,Windows.Foundation,ContentType=WindowsRuntime]
$asTask = [System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {
    $_.Name -eq 'AsTask' -and $_.IsGenericMethod -and
    $_.GetGenericArguments().Length -eq 1 -and $_.GetParameters().Length -eq 1 -and
    $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1'
} | Select-Object -First 1
function Await-Operation($Operation, $ResultType) {
    $task = $asTask.MakeGenericMethod($ResultType).Invoke($null, @($Operation))
    $task.Wait()
    return $task.Result
}
$file = Await-Operation ([Windows.Storage.StorageFile]::GetFileFromPathAsync($ImagePath)) ([Windows.Storage.StorageFile])
$stream = Await-Operation ($file.OpenAsync([Windows.Storage.FileAccessMode]::Read)) ([Windows.Storage.Streams.IRandomAccessStream])
try {
    $decoder = Await-Operation ([Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($stream)) ([Windows.Graphics.Imaging.BitmapDecoder])
    $bitmap = Await-Operation ($decoder.GetSoftwareBitmapAsync()) ([Windows.Graphics.Imaging.SoftwareBitmap])
    try {
        $language = New-Object Windows.Globalization.Language('zh-Hans-CN')
        $engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromLanguage($language)
        if ($null -eq $engine) { throw 'Install the Windows Simplified Chinese OCR language capability.' }
        if ($bitmap.PixelWidth -gt [Windows.Media.Ocr.OcrEngine]::MaxImageDimension -or
            $bitmap.PixelHeight -gt [Windows.Media.Ocr.OcrEngine]::MaxImageDimension) {
            throw 'Image exceeds Windows OCR limits; lower render dpi.'
        }
        $result = Await-Operation ($engine.RecognizeAsync($bitmap)) ([Windows.Media.Ocr.OcrResult])
        $lines = @($result.Lines | ForEach-Object {
            $line = $_
            $words = @($line.Words | ForEach-Object {
                $rect = $_.BoundingRect
                @{text=$_.Text; x=$rect.X; y=$rect.Y; width=$rect.Width; height=$rect.Height}
            })
            @{text=$line.Text; words=$words}
        })
        $data = @{engine='Windows.Media.Ocr'; language='zh-Hans-CN'; text=$result.Text;
                  text_angle=$result.TextAngle; width=$bitmap.PixelWidth; height=$bitmap.PixelHeight; lines=$lines}
        [System.IO.File]::WriteAllText($OutputPath, ($data | ConvertTo-Json -Depth 10), (New-Object System.Text.UTF8Encoding($false)))
    } finally { if ($null -ne $bitmap) { $bitmap.Dispose() } }
} finally { $stream.Dispose() }
