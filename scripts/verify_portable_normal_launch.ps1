param(
    [Parameter(Mandatory = $true)]
    [string]$PortableRoot,
    [Parameter(Mandatory = $true)]
    [string]$ScreenshotPath,
    [Parameter(Mandatory = $true)]
    [string]$ResultPath,
    [ValidateRange(10, 60)]
    [int]$TimeoutSeconds = 30
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Add-Type -AssemblyName System.Drawing
Add-Type -AssemblyName System.Windows.Forms
Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;
using System.Text;

public static class FlatShotNativeWindow {
    public delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);

    [StructLayout(LayoutKind.Sequential)]
    public struct RECT {
        public int Left;
        public int Top;
        public int Right;
        public int Bottom;
    }

    [DllImport("user32.dll")]
    public static extern bool EnumWindows(EnumWindowsProc callback, IntPtr lParam);

    [DllImport("user32.dll")]
    public static extern bool IsWindowVisible(IntPtr hWnd);

    [DllImport("user32.dll")]
    public static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint processId);

    [DllImport("user32.dll", CharSet = CharSet.Unicode)]
    public static extern int GetWindowText(IntPtr hWnd, StringBuilder text, int count);

    [DllImport("user32.dll")]
    public static extern bool GetWindowRect(IntPtr hWnd, out RECT rect);

    [DllImport("user32.dll")]
    public static extern bool SetForegroundWindow(IntPtr hWnd);

    [DllImport("user32.dll")]
    public static extern bool ShowWindowAsync(IntPtr hWnd, int command);

    [DllImport("user32.dll")]
    public static extern bool PostMessage(IntPtr hWnd, uint message, IntPtr wParam, IntPtr lParam);
}
"@

function Get-NamedProcessSnapshot {
    param([string[]]$Names)
    $items = @()
    foreach ($name in $Names) {
        $items += @(Get-Process -Name $name -ErrorAction SilentlyContinue)
    }
    return @($items | Sort-Object Id -Unique)
}

function Get-FreeTcpPort {
    $probe = [Net.Sockets.TcpListener]::new([Net.IPAddress]::Loopback, 0)
    $probe.Start()
    try {
        return ([Net.IPEndPoint]$probe.LocalEndpoint).Port
    }
    finally {
        $probe.Stop()
    }
}

function Get-VisibleWindows {
    param([int[]]$ProcessIds)
    $wanted = [System.Collections.Generic.HashSet[int]]::new()
    foreach ($id in $ProcessIds) {
        [void]$wanted.Add($id)
    }
    $windows = [System.Collections.Generic.List[object]]::new()
    $callback = [FlatShotNativeWindow+EnumWindowsProc]{
        param([IntPtr]$handle, [IntPtr]$unused)
        $owner = [uint32]0
        [void][FlatShotNativeWindow]::GetWindowThreadProcessId($handle, [ref]$owner)
        if ($wanted.Contains([int]$owner) -and [FlatShotNativeWindow]::IsWindowVisible($handle)) {
            $titleBuffer = [System.Text.StringBuilder]::new(512)
            [void][FlatShotNativeWindow]::GetWindowText($handle, $titleBuffer, $titleBuffer.Capacity)
            $windows.Add([pscustomobject]@{
                Handle = $handle.ToInt64()
                ProcessId = [int]$owner
                Title = $titleBuffer.ToString()
            })
        }
        return $true
    }
    [void][FlatShotNativeWindow]::EnumWindows($callback, [IntPtr]::Zero)
    return @($windows)
}

function Get-OwnedListenerPorts {
    param([int[]]$ProcessIds)
    if (-not $ProcessIds) {
        return @()
    }
    $ports = foreach ($id in $ProcessIds) {
        Get-NetTCPConnection -State Listen -OwningProcess $id -ErrorAction SilentlyContinue |
            Where-Object { $_.LocalAddress -in @("127.0.0.1", "::1") } |
            Select-Object -ExpandProperty LocalPort
    }
    return @($ports | Sort-Object -Unique)
}

function Invoke-LocalHttp {
    param([string]$Uri)
    try {
        $response = Invoke-WebRequest -Uri $Uri -Method Get -TimeoutSec 2 -MaximumRedirection 0 -NoProxy
        return [pscustomobject]@{
            Status = [int]$response.StatusCode
            Content = [string]$response.Content
        }
    }
    catch {
        return $null
    }
}

function Find-LocalEndpoints {
    param([int[]]$Ports)
    $frontend = $null
    $bridge = $null
    foreach ($port in $Ports) {
        $healthUrl = "http://127.0.0.1:$port/health"
        $health = Invoke-LocalHttp -Uri $healthUrl
        if ($null -ne $health -and $health.Status -eq 200) {
            try {
                $payload = $health.Content | ConvertFrom-Json
                if ($payload.ok -eq $true) {
                    $bridge = [pscustomobject]@{ status = 200; url = $healthUrl }
                }
            }
            catch {
            }
        }

        $frontendUrl = "http://127.0.0.1:$port/"
        $root = Invoke-LocalHttp -Uri $frontendUrl
        if ($null -ne $root -and $root.Status -eq 200 -and $root.Content -match "(?i)<(?:!doctype|html)|FlatShot") {
            $frontend = [pscustomobject]@{ status = 200; url = $frontendUrl }
        }
    }
    return [pscustomobject]@{ Frontend = $frontend; Bridge = $bridge }
}

function Save-WindowScreenshot {
    param([long]$Handle, [string]$Path, [int]$RenderTimeoutSeconds = 15)
    $rect = [FlatShotNativeWindow+RECT]::new()
    if (-not [FlatShotNativeWindow]::GetWindowRect([IntPtr]$Handle, [ref]$rect)) {
        throw "GetWindowRect failed for handle $Handle."
    }
    $virtualScreen = [System.Windows.Forms.SystemInformation]::VirtualScreen
    $left = [Math]::Max($rect.Left, $virtualScreen.Left)
    $top = [Math]::Max($rect.Top, $virtualScreen.Top)
    $right = [Math]::Min($rect.Right, $virtualScreen.Right)
    $bottom = [Math]::Min($rect.Bottom, $virtualScreen.Bottom)
    $width = $right - $left
    $height = $bottom - $top
    if ($width -lt 320 -or $height -lt 200) {
        throw "FlatShot window is unexpectedly small: ${width}x${height}."
    }

    $directory = Split-Path -Parent $Path
    if ($directory) {
        New-Item -ItemType Directory -Path $directory -Force | Out-Null
    }
    [void][FlatShotNativeWindow]::ShowWindowAsync([IntPtr]$Handle, 9)
    [void][FlatShotNativeWindow]::SetForegroundWindow([IntPtr]$Handle)
    $captureDeadline = (Get-Date).AddSeconds($RenderTimeoutSeconds)
    $attempts = 0
    do {
        $attempts += 1
        Start-Sleep -Milliseconds 750
        $bitmap = [System.Drawing.Bitmap]::new($width, $height, [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
        $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
        try {
            $graphics.CopyFromScreen($left, $top, 0, 0, [System.Drawing.Size]::new($width, $height))
            $bitmap.Save($Path, [System.Drawing.Imaging.ImageFormat]::Png)
        }
        finally {
            $graphics.Dispose()
        }
        $colors = [System.Collections.Generic.HashSet[int]]::new()
        $minimumBrightness = 1.0
        $maximumBrightness = 0.0
        $stepX = [Math]::Max(1, [int]($width / 24))
        $stepY = [Math]::Max(1, [int]($height / 18))
        for ($y = 0; $y -lt $height; $y += $stepY) {
            for ($x = 0; $x -lt $width; $x += $stepX) {
                $color = $bitmap.GetPixel($x, $y)
                [void]$colors.Add($color.ToArgb())
                $brightness = [double]$color.GetBrightness()
                $minimumBrightness = [Math]::Min($minimumBrightness, $brightness)
                $maximumBrightness = [Math]::Max($maximumBrightness, $brightness)
            }
        }
        $nonUniform = $colors.Count -gt 8 -and ($maximumBrightness - $minimumBrightness) -gt 0.04
        $bitmap.Dispose()
        if ($nonUniform -or (Get-Date) -ge $captureDeadline) {
            return [pscustomobject]@{
                path = [IO.Path]::GetFullPath($Path)
                sizeBytes = (Get-Item -LiteralPath $Path).Length
                nonUniform = $nonUniform
                clientContentDetected = $false
                width = $width
                height = $height
                sampledColors = $colors.Count
                captureMethod = "CopyFromScreen"
                attempts = $attempts
            }
        }
    } while ((Get-Date) -lt $captureDeadline)
}

function Test-ScreenshotContent {
    param([string]$Path)
    $bitmap = [System.Drawing.Bitmap]::FromFile($Path)
    try {
        $colors = [System.Collections.Generic.HashSet[int]]::new()
        $minimumBrightness = 1.0
        $maximumBrightness = 0.0
        $stepX = [Math]::Max(1, [int]($bitmap.Width / 32))
        $stepY = [Math]::Max(1, [int]($bitmap.Height / 24))
        for ($y = 0; $y -lt $bitmap.Height; $y += $stepY) {
            for ($x = 0; $x -lt $bitmap.Width; $x += $stepX) {
                $color = $bitmap.GetPixel($x, $y)
                [void]$colors.Add($color.ToArgb())
                $brightness = [double]$color.GetBrightness()
                $minimumBrightness = [Math]::Min($minimumBrightness, $brightness)
                $maximumBrightness = [Math]::Max($maximumBrightness, $brightness)
            }
        }
        return [pscustomobject]@{
            width = $bitmap.Width
            height = $bitmap.Height
            sampledColors = $colors.Count
            nonUniform = ($colors.Count -gt 16 -and ($maximumBrightness - $minimumBrightness) -gt 0.08)
        }
    }
    finally {
        $bitmap.Dispose()
    }
}

function Invoke-DevToolsCommand {
    param([string]$WebSocketUrl, [hashtable]$Message)
    $socket = [Net.WebSockets.ClientWebSocket]::new()
    $timeout = [Threading.CancellationTokenSource]::new(10000)
    try {
        $socket.ConnectAsync([Uri]$WebSocketUrl, $timeout.Token).GetAwaiter().GetResult()
        $json = $Message | ConvertTo-Json -Depth 6 -Compress
        $bytes = [Text.Encoding]::UTF8.GetBytes($json)
        $socket.SendAsync(
            [ArraySegment[byte]]::new($bytes),
            [Net.WebSockets.WebSocketMessageType]::Text,
            $true,
            $timeout.Token
        ).GetAwaiter().GetResult()

        $buffer = [byte[]]::new(65536)
        $stream = [IO.MemoryStream]::new()
        try {
            do {
                $received = $socket.ReceiveAsync([ArraySegment[byte]]::new($buffer), $timeout.Token).GetAwaiter().GetResult()
                $stream.Write($buffer, 0, $received.Count)
            } while (-not $received.EndOfMessage)
            return [Text.Encoding]::UTF8.GetString($stream.ToArray()) | ConvertFrom-Json
        }
        finally {
            $stream.Dispose()
        }
    }
    finally {
        if ($socket.State -eq [Net.WebSockets.WebSocketState]::Open) {
            $socket.CloseAsync(
                [Net.WebSockets.WebSocketCloseStatus]::NormalClosure,
                "FlatShot verification complete",
                [Threading.CancellationToken]::None
            ).GetAwaiter().GetResult()
        }
        $timeout.Dispose()
        $socket.Dispose()
    }
}

function Save-WebViewScreenshot {
    param([int]$DebugPort, [string]$FrontendUrl, [string]$Path, [int]$RenderTimeoutSeconds = 15)
    $deadline = (Get-Date).AddSeconds($RenderTimeoutSeconds)
    $attempts = 0
    $lastError = $null
    do {
        $attempts += 1
        Start-Sleep -Milliseconds 750
        try {
            $targets = @(Invoke-RestMethod -Uri "http://127.0.0.1:$DebugPort/json/list" -TimeoutSec 2 -NoProxy)
            $target = $targets | Where-Object {
                $_.type -eq "page" -and [string]$_.url -like "$FrontendUrl*"
            } | Select-Object -First 1
            if ($null -eq $target) {
                $target = $targets | Where-Object { $_.type -eq "page" } | Select-Object -First 1
            }
            if ($null -eq $target -or -not $target.webSocketDebuggerUrl) {
                throw "No WebView2 page target is available on diagnostic port $DebugPort."
            }
            $response = Invoke-DevToolsCommand -WebSocketUrl $target.webSocketDebuggerUrl -Message @{
                id = 1
                method = "Page.captureScreenshot"
                params = @{ format = "png"; fromSurface = $true; captureBeyondViewport = $false }
            }
            if (-not $response.result.data) {
                throw "WebView2 did not return screenshot data."
            }
            $directory = Split-Path -Parent $Path
            if ($directory) {
                New-Item -ItemType Directory -Path $directory -Force | Out-Null
            }
            [IO.File]::WriteAllBytes($Path, [Convert]::FromBase64String([string]$response.result.data))
            $analysis = Test-ScreenshotContent -Path $Path
            if ($analysis.nonUniform -or (Get-Date) -ge $deadline) {
                return [pscustomobject]@{
                    path = [IO.Path]::GetFullPath($Path)
                    sizeBytes = (Get-Item -LiteralPath $Path).Length
                    nonUniform = $analysis.nonUniform
                    clientContentDetected = $analysis.nonUniform
                    width = $analysis.width
                    height = $analysis.height
                    sampledColors = $analysis.sampledColors
                    captureMethod = "WebView2 DevTools Protocol"
                    attempts = $attempts
                    targetUrl = [string]$target.url
                }
            }
        }
        catch {
            $lastError = $_.Exception.Message
        }
    } while ((Get-Date) -lt $deadline)
    throw "Could not capture rendered WebView2 content: $lastError"
}

function Read-NewLogContent {
    param([string]$Path, [long]$OriginalLength)
    if (-not (Test-Path -LiteralPath $Path)) {
        return ""
    }
    $content = [IO.File]::ReadAllText($Path)
    if ($OriginalLength -ge $content.Length) {
        return ""
    }
    return $content.Substring([int]$OriginalLength)
}

$portable = [IO.Path]::GetFullPath($PortableRoot).TrimEnd("\")
$executable = Join-Path $portable "FlatShot.exe"
$runtimeLog = Join-Path $portable "data\logs\runtime.log"
$resultFile = [IO.Path]::GetFullPath($ResultPath)
$collectorErrors = [System.Collections.Generic.List[string]]::new()
$process = $null
$window = $null
$endpoints = [pscustomobject]@{ Frontend = $null; Bridge = $null }
$webViewProcesses = @()
$newPythonProcesses = @()
$screenshot = [pscustomobject]@{ path = [IO.Path]::GetFullPath($ScreenshotPath); sizeBytes = 0; nonUniform = $false; clientContentDetected = $false; width = 0; height = 0 }
$desktopScreenshot = $null
$stayedAlive = $false
$exitCodeBeforeCleanup = $null
$gracefulCloseRequested = $false
$forceKillUsed = $false
$listenerPorts = @()
$remainingPorts = @()
$remainingSession = @()
$systemRoot = [Environment]::GetEnvironmentVariable("SystemRoot", "Process").TrimEnd("\")
$cleanPath = @($systemRoot, "$systemRoot\System32", "$systemRoot\System32\Wbem") -join ";"
$logBeforeLength = if (Test-Path -LiteralPath $runtimeLog) { (Get-Item -LiteralPath $runtimeLog).Length } else { 0 }
$launchTime = Get-Date
$preexistingWebView = @(Get-NamedProcessSnapshot -Names @("msedgewebview2") | Select-Object -ExpandProperty Id)
$preexistingPython = @(Get-NamedProcessSnapshot -Names @("python", "pythonw", "py") | Select-Object -ExpandProperty Id)
$webViewDebugPort = Get-FreeTcpPort

try {
    if (-not (Test-Path -LiteralPath $executable -PathType Leaf)) {
        throw "FlatShot.exe is missing from extracted portable root: $executable"
    }

    $savedEnvironment = @{}
    foreach ($name in @("PYTHONHOME", "PYTHONPATH", "VIRTUAL_ENV", "PATH", "WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS")) {
        $savedEnvironment[$name] = [Environment]::GetEnvironmentVariable($name, "Process")
    }
    try {
        foreach ($name in @("PYTHONHOME", "PYTHONPATH", "VIRTUAL_ENV")) {
            [Environment]::SetEnvironmentVariable($name, $null, "Process")
        }
        [Environment]::SetEnvironmentVariable("PATH", $cleanPath, "Process")
        [Environment]::SetEnvironmentVariable(
            "WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS",
            "--remote-debugging-port=$webViewDebugPort",
            "Process"
        )
        $process = Start-Process -FilePath $executable -WorkingDirectory $portable -PassThru
    }
    finally {
        foreach ($name in $savedEnvironment.Keys) {
            [Environment]::SetEnvironmentVariable($name, $savedEnvironment[$name], "Process")
        }
    }

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    do {
        Start-Sleep -Milliseconds 400
        $process.Refresh()
        if ($process.HasExited) {
            $exitCodeBeforeCleanup = $process.ExitCode
            break
        }
        $sessionProcesses = @(Get-NamedProcessSnapshot -Names @("FlatShot") | Where-Object { $_.StartTime -ge $launchTime.AddSeconds(-2) })
        $sessionIds = @($sessionProcesses | Select-Object -ExpandProperty Id)
        if ($process.Id -notin $sessionIds) {
            $sessionIds += $process.Id
        }
        $listenerPorts = @(Get-OwnedListenerPorts -ProcessIds $sessionIds)
        $endpoints = Find-LocalEndpoints -Ports $listenerPorts
        $window = @(Get-VisibleWindows -ProcessIds $sessionIds | Where-Object { $_.Title -match "(?i)FlatShot" } | Select-Object -First 1)
        if ($window.Count -gt 0) {
            $window = $window[0]
        }
        else {
            $window = $null
        }
        $webViewProcesses = @(Get-NamedProcessSnapshot -Names @("msedgewebview2") | Where-Object {
            $_.Id -notin $preexistingWebView -and $_.StartTime -ge $launchTime.AddSeconds(-2)
        })
    } while ((Get-Date) -lt $deadline -and ($null -eq $endpoints.Frontend -or $null -eq $endpoints.Bridge -or $null -eq $window -or $webViewProcesses.Count -eq 0))

    $process.Refresh()
    $stayedAlive = -not $process.HasExited
    if (-not $stayedAlive) {
        $exitCodeBeforeCleanup = $process.ExitCode
    }
    $newPythonProcesses = @(Get-NamedProcessSnapshot -Names @("python", "pythonw", "py") | Where-Object {
        $_.Id -notin $preexistingPython -and $_.StartTime -ge $launchTime.AddSeconds(-2)
    })
    if ($null -ne $window) {
        Start-Sleep -Seconds 3
        $desktopPath = Join-Path (Split-Path -Parent $ScreenshotPath) "flatshot-normal-launch-desktop.png"
        $desktopScreenshot = Save-WindowScreenshot -Handle $window.Handle -Path $desktopPath -RenderTimeoutSeconds 2
        if ($null -ne $endpoints.Frontend) {
            $screenshot = Save-WebViewScreenshot `
                -DebugPort $webViewDebugPort `
                -FrontendUrl $endpoints.Frontend.url.TrimEnd("/") `
                -Path $ScreenshotPath
        }
    }
}
catch {
    $collectorErrors.Add($_.Exception.ToString())
}
finally {
    try {
        if ($null -ne $window) {
            $gracefulCloseRequested = [FlatShotNativeWindow]::PostMessage([IntPtr]$window.Handle, 0x0010, [IntPtr]::Zero, [IntPtr]::Zero)
        }
        if ($null -ne $process -and -not $process.HasExited) {
            if (-not $process.WaitForExit(10000)) {
                $forceKillUsed = $true
                Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
            }
        }
        $remainingSession = @(Get-NamedProcessSnapshot -Names @("FlatShot") | Where-Object { $_.StartTime -ge $launchTime.AddSeconds(-2) })
        if ($remainingSession.Count -gt 0) {
            $forceKillUsed = $true
            $remainingSession | Stop-Process -Force -ErrorAction SilentlyContinue
        }
        $cleanupDeadline = (Get-Date).AddSeconds(10)
        do {
            Start-Sleep -Milliseconds 250
            $remainingSession = @(Get-NamedProcessSnapshot -Names @("FlatShot") | Where-Object { $_.StartTime -ge $launchTime.AddSeconds(-2) })
            $remainingPorts = @(if ($null -ne $process) { Get-OwnedListenerPorts -ProcessIds @($process.Id) })
        } while ((Get-Date) -lt $cleanupDeadline -and ($remainingSession.Count -gt 0 -or $remainingPorts.Count -gt 0))
    }
    catch {
        $collectorErrors.Add("Cleanup: $($_.Exception)")
    }
}

$newLog = Read-NewLogContent -Path $runtimeLog -OriginalLength $logBeforeLength
$fallbackDetected = $newLog -match "(?m)^\[[^\]]+\] Native desktop window\s*$"
$startupErrors = @()
if ($newLog -match "(?m)^\[[^\]]+\] (Portable launcher|Portable smoke)\s*$") {
    $startupErrors = @($newLog.Trim())
}
$windowMode = if ($fallbackDetected) { "browser fallback" } elseif ($webViewProcesses.Count -gt 0 -and $null -ne $window) { "edgechromium native window" } else { "undetermined" }
$remainingSession = @(Get-NamedProcessSnapshot -Names @("FlatShot") | Where-Object { $_.StartTime -ge $launchTime.AddSeconds(-2) })
$remainingPorts = @(if ($null -ne $process) { Get-OwnedListenerPorts -ProcessIds @($process.Id) })
$resolvedExecutable = [IO.Path]::GetFullPath($executable)
$insidePortable = $resolvedExecutable.StartsWith($portable + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)

$result = [ordered]@{
    schemaVersion = 1
    executable = $resolvedExecutable
    portableRoot = $portable
    launchedAtUtc = $launchTime.ToUniversalTime().ToString("o")
    collectorErrors = @($collectorErrors)
    process = [ordered]@{
        started = ($null -ne $process)
        processId = if ($null -ne $process) { $process.Id } else { $null }
        stayedAlive = $stayedAlive
        exitCodeBeforeCleanup = $exitCodeBeforeCleanup
    }
    environment = [ordered]@{
        pythonHomeCleared = $true
        pythonPathCleared = $true
        virtualEnvCleared = $true
        pathSanitized = $true
        sanitizedPath = $cleanPath
        executableInPortableRoot = $insidePortable
        externalPythonProcesses = @($newPythonProcesses | ForEach-Object { [ordered]@{ name = $_.ProcessName; pid = $_.Id } })
    }
    http = [ordered]@{
        discoveredListenerPorts = @($listenerPorts)
        frontend = if ($null -ne $endpoints.Frontend) { $endpoints.Frontend } else { [ordered]@{ status = $null; url = $null } }
        bridge = if ($null -ne $endpoints.Bridge) { $endpoints.Bridge } else { [ordered]@{ status = $null; url = $null } }
    }
    window = if ($null -ne $window) {
        [ordered]@{ visible = $true; title = $window.Title; handle = $window.Handle; processId = $window.ProcessId }
    } else {
        [ordered]@{ visible = $false; title = ""; handle = 0; processId = $null }
    }
    webView2 = [ordered]@{
        detected = ($webViewProcesses.Count -gt 0)
        temporallyRelated = ($webViewProcesses.Count -gt 0)
        relation = if ($webViewProcesses.Count -gt 0) { "started during FlatShot session" } else { "not detected" }
        pids = @($webViewProcesses | Select-Object -ExpandProperty Id)
    }
    windowMode = $windowMode
    runtimeLog = [ordered]@{
        path = $runtimeLog
        fallbackDetected = $fallbackDetected
        startupErrors = $startupErrors
        newContent = $newLog
    }
    screenshot = $screenshot
    desktopScreenshot = $desktopScreenshot
    cleanup = [ordered]@{
        gracefulCloseRequested = $gracefulCloseRequested
        forceKillUsed = $forceKillUsed
        flatShotOrphans = @($remainingSession | Select-Object -ExpandProperty Id)
        listenerPortsRemaining = @($remainingPorts)
    }
}

$resultDirectory = Split-Path -Parent $resultFile
if ($resultDirectory) {
    New-Item -ItemType Directory -Path $resultDirectory -Force | Out-Null
}
$result | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $resultFile -Encoding utf8
$result | ConvertTo-Json -Depth 8
