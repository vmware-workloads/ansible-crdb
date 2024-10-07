# Load required assembly for forms
Add-Type -AssemblyName System.Windows.Forms

# Define the file path for the JSON file
$jsonFilePath = "config.json"
$pythonInstaller = "vro_installer.py"

# Initialize the pre-populated text values as an empty hash table
$prePopulatedData = @{}

# Check if the JSON file exists
if (Test-Path $jsonFilePath) {
    # Read the existing JSON file
    $jsonContent = Get-Content -Path $jsonFilePath -Raw | ConvertFrom-Json


    
    # Populate prePopulatedData with the fields from the JSON
    $prePopulatedData = ($jsonContent.psobject.properties) | ForEach-Object -Process {$_.Name}

    write-output($prePopulatedData)
}

# -----

# check for python - otherwise say to install

# 



# Create a form
$form = New-Object System.Windows.Forms.Form
$form.Text = "vRO Elements Installer
$form.Width = 500
$form.Height = 400 + (40 * $prePopulatedData.Count)

# Create a hash table to hold the textboxes for each field
$textBoxes = @{}

# Position counters
$yPos = 10
$labelWidth = 150
$boxWidth = 300

# Create labels and text boxes dynamically based on keys in prePopulatedData
foreach ($key in $prePopulatedData) {
    # Create a label for each key
    $label = New-Object System.Windows.Forms.Label
    $label.Text = "$key"
    $label.Width = $labelWidth
    $label.Location = New-Object System.Drawing.Point(10, $yPos)
    $form.Controls.Add($label)

    # Create a text box for each value
    $textBox = New-Object System.Windows.Forms.TextBox
    $textBox.Width = $boxWidth
    $textBox.Location = New-Object System.Drawing.Point(170, $yPos)
    # Handle null values
    $textBox.Text = if ($jsonContent.$key -eq $null) { "" } else { $jsonContent.$key }
    $form.Controls.Add($textBox)

    # Store the textBox reference in the hash table
    $textBoxes[$key] = $textBox

    # Increment position for next set of controls
    $yPos += 40
}

# Create a button to submit
$button = New-Object System.Windows.Forms.Button
$button.Text = "Submit"
$button.Location = New-Object System.Drawing.Point(10, $yPos)
$form.Controls.Add($button)

# Define button click action
$button.Add_Click({
    # Collect the data from all text boxes
    $data = @{}
    foreach ($key in $textBoxes.Keys) {
        $data[$key] = $textBoxes[$key].Text
    }

    # Convert to JSON and write to file
    $json = $data | ConvertTo-Json
    $json | Out-File -FilePath $jsonFilePath

    # Close the form after submitting
    $form.Close()
})

# Show the form
$form.ShowDialog()


## launch python script