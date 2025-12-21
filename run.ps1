Param(
    [Parameter(ValueFromRemainingArguments=$true)]
    [string[]]$Args
)
if ($Args.Count -eq 0) { Write-Host "Uso: run <comando> <args>"; exit 1 }
$first = $Args[0]
$rest = if ($Args.Count -gt 1) { $Args[1..($Args.Count-1)] } else { @() }
if ($first -ieq 'streamlit') {
    python -m streamlit run @rest
} else {
    & $first @rest
}
