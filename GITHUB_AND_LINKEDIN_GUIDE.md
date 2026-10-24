# GitHub and LinkedIn launch guide

## GitHub: upload the editable program
1. Sign in to https://github.com and click **+ > New repository**.
2. Repository name: `FAHU-Academic-Studio`.
3. Choose **Public** only if you have the right to publish all source files. Do **not** select “Add README” because this package already contains one.
4. Extract the v4.1 ZIP to a folder, open PowerShell in that folder and run:

```powershell
git init
git add .
git commit -m "FAHU Academic Studio v4.1: ASHRAE equation audit"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/FAHU-Academic-Studio.git
git push -u origin main
```

Replace `YOUR-USERNAME`. If prompted, sign in through Git Credential Manager. Install Git for Windows from https://git-scm.com/downloads/win if `git` is not recognized.

**Alternative without Git:** Open your new repository in the browser > **Add file > Upload files** > upload project source and documentation (not generated `.exe` or copyrighted ASHRAE PDF) > **Commit changes**.

## Release an executable
Run `BUILD_EXE.bat` on Windows, verify the result and its antivirus behavior. On GitHub: **Releases > Draft a new release** > tag `v4.1.0` > upload the verified `dist/FAHU_Academic_V4_1.exe` > explain limitations > Publish release. Do not publish a build you have not tested.

## LinkedIn
Post a screenshot of the working application (ideally the equation audit tab), one recovery schematic and a sample report page with private data removed. Link to the GitHub repository. See the suggested post in the chat.

## Suggested tags
#HVAC #HeatRecovery #MechanicalEngineering #ASHRAE #Python #EngineeringSoftware

## Before publishing
- Confirm intellectual property ownership and any university/employer requirements.
- Do not include the ASHRAE Handbook PDF in the repository.
- Do not use the ASHRAE logo or imply endorsement/certification.
- Verify numerical results and disclose the model's limitations.
- Consider a license; absent a license, others cannot generally reuse or modify the code beyond legal exceptions.
